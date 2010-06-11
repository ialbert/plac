##########################     LICENCE     ###############################
##
##   Copyright (c) 2010, Michele Simionato
##   All rights reserved.
##
##   Redistributions of source code must retain the above copyright 
##   notice, this list of conditions and the following disclaimer.
##   Redistributions in bytecode form must reproduce the above copyright
##   notice, this list of conditions and the following disclaimer in
##   the documentation and/or other materials provided with the
##   distribution. 

##   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
##   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
##   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
##   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
##   HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
##   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
##   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
##   OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
##   TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
##   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
##   DAMAGE.

"""
plac, the easiest Command Line Arguments Parser in the world.
See plac/doc.html for the documentation.
"""
# this module should be kept Python 2.3 compatible

__version__ = '0.4.3'

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
        elif hasattr(obj, '__iter__') and not isinstance(obj, str):
            return cls(*obj)
        return cls(obj)
    from_ = classmethod(from_)

NONE = object() # sentinel use to signal the absence of a default

valid_attrs = getfullargspec(argparse.ArgumentParser.__init__).args[1:]

class PlacHelpFormatter(argparse.HelpFormatter):
    "Custom HelpFormatter which does not displau the default value twice"

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return self._metavar_formatter(action, action.dest)(1)[0]
        long_short = tuple(action.option_strings)
        if action.nargs == 0: # format is -s, --long
            return '%s, %s' % long_short    
        else: # format is -s, --long ARGS
            default = action.dest.upper()
            args_string = self._format_args(action, default)
            return '%s, %s %s' % (long_short + (args_string,))
 
def parser_from(func):
    """
    Extract the arguments from the attributes of the passed function and
    return an ArgumentParser instance.
    """
    short_prefix = getattr(func, 'short_prefix', '-')
    long_prefix = getattr(func, 'long_prefix', '--')
    attrs = dict(description=func.__doc__,
                 formatter_class=PlacHelpFormatter)
    for n, v in vars(func).items():
        if n in valid_attrs:
            attrs[n] = v
    p = func.parser = argparse.ArgumentParser(**attrs)
    f = p.argspec = getfullargspec(func)
    defaults = f.defaults or ()
    n_args = len(f.args)
    n_defaults = len(defaults)
    alldefaults = (NONE,) * (n_args - n_defaults) + defaults
    for name, default in zip(f.args, alldefaults):
        a = Annotation.from_(f.annotations.get(name, ()))
        metavar = a.metavar
        if default is NONE:
            dflt = None
        else:
            dflt = default
        if a.kind in ('option', 'flag'):
            short = short_prefix + (a.abbrev or name[0])
            long = long_prefix + name
        elif default is NONE: # required argument
            p.add_argument(name, help=a.help, type=a.type, choices=a.choices,
                           metavar=metavar)
        else: # default argument
            p.add_argument(name, nargs='?', help=a.help, default=dflt, 
                           type=a.type, choices=a.choices, metavar=metavar)
        if a.kind == 'option':
            if default is not NONE:
                metavar = metavar or str(default)
            p.add_argument(short, long, help=a.help, default=dflt,
                           type=a.type, choices=a.choices, metavar=metavar)
        elif a.kind == 'flag':
            if default is not NONE and default is not False:
                raise TypeError('Flag %r wants default False, got %r' %
                                (name, default))
            p.add_argument(short, long, action='store_true', help=a.help)
    if f.varargs:
        a = Annotation.from_(f.annotations.get(f.varargs, ()))
        p.add_argument(f.varargs, nargs='*', help=a.help, default=[],
                       type=a.type, metavar=a.metavar)
    if f.varkw:
        a = Annotation.from_(f.annotations.get(f.varkw, ()))
        p.add_argument(f.varkw, nargs='*', help=a.help, default={},
                       type=a.type, metavar=a.metavar)
    return p

def extract_kwargs(args):
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

def call(func, arglist=sys.argv[1:]):
    """
    Parse the given arglist by using an argparser inferred from the
    annotations of the given function (the main function of the script)
    and call that function with the parsed arguments. The user can
    provide a custom parse_annotation hook or replace the default one.
    """
    p = parser_from(func)
    if p.argspec.varkw:
        arglist, kwargs = extract_kwargs(arglist)
    else:
        kwargs = {}
    argdict = vars(p.parse_args(arglist))
    args = [argdict[a] for a in p.argspec.args]
    varargs = argdict.get(p.argspec.varargs, [])
    collision = set(p.argspec.args) & set(kwargs)
    if collision:
        p.error('colliding keyword arguments: %s' % ' '.join(collision))
    return func(*(args + varargs), **kwargs)
