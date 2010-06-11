import os, sys, cmd, shlex
import plac

def cmd_interface(obj):
    "Returns a cmd.Cmd wrapper over the command container"
    dic = {}
    for command in obj.commands:
        method = getattr(obj, command)
        def do_func(self, line, command=command):
            args = [command] + shlex.split(line)
            try:
                for output in plac.call(obj, args):
                    print(output)
            except SystemExit:
                print(e)
            except Exception:
                print('%s: %s' % (e.__class__.__name__, e))
        do_func.__doc__ = method.__doc__
        if sys.version >= '2.4':
            do_func.__name__ = method.__name__
        dic['do_' + command] = do_func
    clsname = '_%s_' % obj.__class__.__name__
    cls = type(clsname, (cmd.Cmd, object), dic)
    return cls()

# requires Python 2.5+
class Interpreter(object):
    """
    The safety_net is a function taking a parsing function and a list of
    arguments and applying the first to the second by managing some class
    of exceptions.
    """
    def __init__(self, obj, safety_net=lambda parse, arglist: parse(arglist),
                 commentchar='#'):
        self.obj = obj
        self.safety_net = safety_net
        self.commentchar = commentchar
        self.interpreter = None
        self.p = plac.parser_from(obj)
        self.p.error = lambda msg: sys.exit(msg) # patch the parser

    def __enter__(self):
        self.interpreter = self._make_interpreter()
        self.interpreter.send(None)
        return self

    def send(self, line):
        """
        Send a line to the underlying interpreter. 
        Return a string or None for comment lines.
        The line should end with a newline.
        """
        return self.interpreter.send(line)

    def close(self):
        self.interpreter.close()

    def __exit__(self, *exc):
        self.close()

    def _make_interpreter(self):
        enter = getattr(self.obj, '__enter__', lambda : None)
        exit = getattr(self.obj, '__exit__', lambda a1, a2, a3: None)
        enter()
        result = None
        prefix = self.p.short_prefix
        try:
            while True:
                line = yield result
                if not line:
                    break
                elif line.startswith(self.commentchar):
                    yield; continue
                arglist = shlex.split(line)
                for i, long_opt in enumerate(arglist):
                    # avoid double prefix in long options
                    if len(long_opt) > 2 and long_opt[0] == prefix:
                        arglist[i] = prefix + long_opt
                try:
                    output = self.safety_net(self.p.parselist, arglist)
                except SystemExit, e:
                    output = [str(e)]
                result = os.linesep.join(output)
        except:
            exit(*sys.exc_info())
            raise
        else:
            exit(None, None, None)

## from cmd.py
# def complete(self, text, state):
#     """Return the next possible completion for 'text'.

#     If a command has not been entered, then complete against command list.
#     Otherwise try to call complete_<command> to get list of completions.
#     """
#     if state == 0:
#         import readline
#         origline = readline.get_line_buffer()
#         line = origline.lstrip()
#         stripped = len(origline) - len(line)
#         begidx = readline.get_begidx() - stripped
#         endidx = readline.get_endidx() - stripped
#         if begidx>0:
#             cmd, args, foo = self.parseline(line)
#             if cmd == '':
#                 compfunc = self.completedefault
#             else:
#                 try:
#                     compfunc = getattr(self, 'complete_' + cmd)
#                 except AttributeError:
#                     compfunc = self.completedefault
#         else:
#             compfunc = self.completenames
#         self.completion_matches = compfunc(text, line, begidx, endidx)
#     try:
#         return self.completion_matches[state]
#     except IndexError:
#         return None

# def readlines(completekey='tab'):
#     if readline:
#         old_completer = readline.get_completer()
#         readline.set_completer(self.complete)
#         readline.parse_and_bind(self.completekey + ": complete")
#     try:
#         while True:
#             try:
#                 yield raw_input('cli> ')
#             except EOFError:
#                 break
#     finally:
#         if readline:
#             readline.set_completer(old_completer)

class Cmds(object):
    commands = 'checkout', 'commit', 'status', 'help'
    quit = False

    @plac.annotations(
        name=('a recognized command', 'positional', None, str, commands))
    def help(self, name):
        return self.p.subp[name].format_help()

    def checkout(self, url):
        return ('checkout', url)

    def commit(self):
        return ('commit')

    @plac.annotations(quiet=('summary information', 'flag'))
    def status(self, quiet):
        return ('status', quiet)

if __name__ == '__main__':
    cmdloop(Cmds())
