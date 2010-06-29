# this module should be kept Python 2.3 compatible
import re, sys, inspect, argparse
if sys.version >= '3':
    from inspect import getfullargspec
else:
    class getfullargspec(object):
        "A quick and dirty replacement for getfullargspec for Python 2.X"
        def __init__(self, f):
            self.args, self.varargs, self.varkw, self.defaults = \
                inspect.getargspec(f)
            self.annotations = getattr(f, '__annotations__', {})
try:
    set
except NameError: # Python 2.3
    from sets import Set as set

def annotations(**ann):
    """
    Returns a decorator annotating a function with the given annotations.
    This is a trick to support function annotations in Python 2.X.
    """
    def annotate(f):
        fas = getfullargspec(f)
        args = fas.args
        if fas.varargs:
            args.append(fas.varargs)
        if fas.varkw:
            args.append(fas.varkw)
        for argname in ann:
            if argname not in args:
                raise NameError(
                    'Annotating non-existing argument: %s' % argname)
        f.__annotations__ = ann
        return f
    return annotate

def is_annotation(obj):
    """
    An object is an annotation object if it has the attributes
    help, kind, abbrev, type, choices, metavar.
    """
    return (hasattr(obj, 'help') and hasattr(obj, 'kind') and 
            hasattr(obj, 'abbrev') and hasattr(obj, 'type')
            and hasattr(obj, 'choices') and hasattr(obj, 'metavar'))

class Annotation(object):
    def __init__(self, help="", kind="positional", abbrev=None, type=None,
                 choices=None, metavar=None):
        assert kind in ('positional', 'option', 'flag'), kind
        if kind == "positional":
            assert abbrev is None, abbrev
        self.help = help
        self.kind = kind
        self.abbrev = abbrev
        self.type = type
        self.choices = choices
        self.metavar = metavar

    def from_(cls, obj):
        "Helper to convert an object into an annotation, if needed"
        if is_annotation(obj):
            return obj # do nothing
        elif hasattr(obj, '__iter__') and not isinstance(obj, basestring):
            return cls(*obj)
        return cls(obj)
    from_ = classmethod(from_)
 
NONE = object() # sentinel use to signal the absence of a default

PARSER_CFG = getfullargspec(argparse.ArgumentParser.__init__).args[1:]
# the default arguments accepted by an ArgumentParser object

def pconf(obj):
    "Extracts the configuration of the underlying ArgumentParser from obj"
    cfg = dict(description=obj.__doc__)
    for name in dir(obj):
        if name in PARSER_CFG: # argument of ArgumentParser
            cfg[name] = getattr(obj, name)
    return cfg

def parser_from(obj):
    """
    obj can be a callable or an object with a .commands attribute.
    Returns an ArgumentParser.
    """ 
    if hasattr(obj, 'func'): # added by the task manager
        obj = obj.func
    if hasattr(obj, 'p'): # the underlying parser has been generated already
        return obj.p
    parser = obj.p = ArgumentParser(**pconf(obj))
    if hasattr(obj, 'commands'): # a command container
        for cmd in obj.commands:
            parser.addsubparser(cmd, getattr(obj, cmd))
        parser.missing = getattr(
            obj, '__missing__',
            lambda name: parser.error('No command %r' % name))
        parser.func = lambda : None
        parser.argspec = getfullargspec(parser.func)
        return parser
    else:
        return parser._populated(obj)

def _extract_kwargs(args):
    "Returns two lists: regular args and name=value args"
    arglist = []
    kwargs = {}
    for arg in args:
        match = re.match(r'([a-zA-Z_]\w*)=', arg)
        if match:
            name = match.group(1)
            kwargs[name] = arg[len(name)+1:]
        else:
            arglist.append(arg)
    return arglist, kwargs

def _match_cmd(abbrev, commands):
    "Extract the command name from an abbreviation or raise a NameError"
    perfect_matches = [name for name in commands if name == abbrev]
    if len(perfect_matches) == 1:
        return perfect_matches[0]
    matches = [name for name in commands if name.startswith(abbrev)]
    n = len(matches)
    if n == 1:
        return matches[0]
    elif n > 1:
        raise NameError(
            'Ambiguous command %r: matching %s' % (abbrev, matches))

class ArgumentParser(argparse.ArgumentParser):
    """
    An ArgumentParser with .func and .argspec attributes, and possibly
    .commands and .subparsers.
    """
    def consume(self, args, ignore_extra=False):
        """Call the underlying function with the args. Works also for
        command containers, by dispatching to the right subparser."""
        arglist = list(args)
        cmd = None
        if hasattr(self, 'subparsers'):
            subp, cmd = self._extract_subparser_cmd(arglist)
            if subp is None and cmd is not None:
                return self.missing(cmd)
            elif subp is not None: # use the subparser
                self = subp
        if self.argspec.varkw:
            arglist, kwargs = _extract_kwargs(arglist)
        else:
            kwargs = {}
        if ignore_extra: # ignore unrecognized arguments
            ns, self.extra_args = self.parse_known_args(arglist)
        else:
            ns = self.parse_args(arglist)
        args = [getattr(ns, a) for a in self.argspec.args]
        varargs = getattr(ns, self.argspec.varargs or '', [])
        collision = set(self.argspec.args) & set(kwargs)
        if collision:
            self.error('colliding keyword arguments: %s' % ' '.join(collision))
        return cmd, self.func(*(args + varargs), **kwargs)

    def _extract_subparser_cmd(self, arglist):
        "Extract the subparser from the first recognized argument"
        prefix = self.prefix_chars[0] 
        name_parser_map = self.subparsers._name_parser_map
        for i, arg in enumerate(arglist):
            if not arg.startswith(prefix):
                cmd = _match_cmd(arg, name_parser_map)
                del arglist[i] 
                return name_parser_map.get(cmd), cmd
        return None, None

    def addsubparser(self, cmd, func):
        "Add a subparser for a command"
        if not hasattr(self, 'subparsers'):
            self.subparsers = self.add_subparsers(
                title='subcommands', help='-h to get additional help')
        subp = self.subparsers.add_parser(cmd, **pconf(func))
        return subp._populated(func)

    def _set_func_argspec(self, obj):
        """Extracts the signature from a callable object and adds an .argspec
        attribute to the parser. Also adds a .func reference to the object."""
        self.func = obj
        if inspect.isfunction(obj):
            self.argspec = getfullargspec(obj)
            obj.p = self
        elif inspect.ismethod(obj):
            self.argspec = getfullargspec(obj)
            obj.im_func.p = self
            del self.argspec.args[0] # remove first argument
        elif inspect.isclass(obj):
            self.argspec = getfullargspec(obj.__init__)
            obj.__init__.im_func.p = self
            del self.argspec.args[0] # remove first argument
        elif hasattr(obj, '__call__'):
            self.argspec = getfullargspec(obj.__call__)
            obj.__call__.im_func.p = self
            del self.argspec.args[0] # remove first argument
        else:
            raise TypeError('Could not determine signature of %r' % obj)

    def _populated(self, func):
        """
        Extract the arguments from the attributes of the passed function
        and return a populated ArgumentParser instance. As a side
        effect, adds a .p attribute to func.
        """
        self._set_func_argspec(func)
        f = self.argspec
        defaults = f.defaults or ()
        n_args = len(f.args)
        n_defaults = len(defaults)
        alldefaults = (NONE,) * (n_args - n_defaults) + defaults
        prefix = self.prefix = getattr(func, 'prefix_chars', '-')[0]
        for name, default in zip(f.args, alldefaults):
            ann = f.annotations.get(name, ())
            a = Annotation.from_(ann)
            metavar = a.metavar
            if default is NONE:
                dflt = None
            else:
                dflt = default
            if a.kind in ('option', 'flag'):
                if a.abbrev:
                    shortlong = (prefix + a.abbrev, prefix*2 + name)
                else:
                    shortlong = (prefix + name,)
            elif default is NONE: # required argument
                self.add_argument(name, help=a.help, type=a.type, 
                                  choices=a.choices, metavar=metavar)
            else: # default argument
                self.add_argument(
                    name, nargs='?', help=a.help, default=dflt, 
                    type=a.type, choices=a.choices, metavar=metavar)
            if a.kind == 'option':
                if default is not NONE:
                    metavar = metavar or str(default)
                self.add_argument(
                    help=a.help, default=dflt, type=a.type,
                    choices=a.choices, metavar=metavar, *shortlong)
            elif a.kind == 'flag':
                if default is not NONE and default is not False:
                    raise TypeError('Flag %r wants default False, got %r' %
                                    (name, default))
                self.add_argument(action='store_true', help=a.help, *shortlong)
        if f.varargs:
            a = Annotation.from_(f.annotations.get(f.varargs, ()))
            self.add_argument(f.varargs, nargs='*', help=a.help, default=[],
                              type=a.type, metavar=a.metavar)
        if f.varkw:
            a = Annotation.from_(f.annotations.get(f.varkw, ()))
            self.add_argument(f.varkw, nargs='*', help=a.help, default={},
                              type=a.type, metavar=a.metavar)
        return self

def iterable(obj):
    "Any object with an __iter__ method which is not a string"
    return hasattr(obj, '__iter__') and not isinstance(obj, basestring)

def call(obj, arglist=sys.argv[1:], ignore_extra=False):
    """
    If obj is a function or a bound method, parse the given arglist 
    by using the argument parser inferred from the annotations of obj
    and call obj with the parsed arguments. 
    If obj is an object with attribute .commands, dispatch to the 
    associated subparser. Returns a list or an atomic object.
    If ignore_extra is True, unrecognized arguments are stored
    in the attribute .extra_args of the associated parser for
    later processing.
    """
    cmd, result = parser_from(obj).consume(arglist, ignore_extra)
    if iterable(result):
        return list(result)
    return result
