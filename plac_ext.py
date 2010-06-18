# this module requires Python 2.5+
from __future__ import with_statement
import os, sys, cmd, shlex, traceback
import plac_core

def cmd_interface(obj):
    "Returns a cmd.Cmd wrapper over the command container"
    i = Interpreter(obj)
    def default(self, line):
        print(i.send(line))
    dic = dict(preloop=lambda self: i.__enter__(),
               postloop=lambda self: i.__exit__(),
               do_EOF=lambda self, line: True,
               default=default)
    for command in obj.commands:
        method = getattr(obj, command)
        def do_func(self, line, command=command):
            print(i.send(command + ' ' + line))
        do_func.__doc__ = method.__doc__
        do_func.__name__ = method.__name__
        dic['do_' + command] = do_func
    clsname = '_%s_' % obj.__class__.__name__
    cls = type(clsname, (cmd.Cmd, object), dic)
    return cls()

def _getoutputs(lines, intlist):
    "helper used in parse_doctest"
    for i, start in enumerate(intlist[:-1]):
        end = intlist[i + 1]
        yield '\n'.join(lines[start+1:end])

class Output(tuple):
    """
    The output returned by the .send method of an Interpreter object.
    Contains the output string (or None if there is an exception)
    and the exception information (exception type, exception, traceback).
    """
    def __new__(cls, outstr, etype, exc, tb):
        self = tuple.__new__(cls, (outstr, etype, exc, tb))
        self.str = outstr
        self.etype = etype
        self.exc = exc
        self.tb = tb
        return self
    def __str__(self):
        "Returns the output string or the error message"
        if self.str is None: # there was an error
            return '%s: %s' % (self.etype.__name__, self.exc)
        else:
            return self.str

class Interpreter(object):
    """
    A context manager with a .send method and a few utility methods:
    execute, test and doctest.
    """
    def __init__(self, obj, commentchar='#'):
        self.obj = obj
        self.commentchar = commentchar
        self.interpreter = None
        self.p = plac_core.parser_from(obj)
        self.p.error = lambda msg: sys.exit(msg) # patch the parser

    def __enter__(self):
        self.interpreter = self._make_interpreter()
        self.interpreter.send(None)
        return self

    def send(self, line):
        "Send a line to the underlying interpreter and return an Output object"
        if self.interpreter is None:
            raise RuntimeError('%r not initialized: probably you forgot to '
                               'use the with statement' % self)
        return self.interpreter.send(line)

    def close(self):
        self.interpreter.close()

    def __exit__(self, *exc):
        self.close()

    def _make_interpreter(self):
        enter = getattr(self.obj, '__enter__', lambda : None)
        exit = getattr(self.obj, '__exit__', lambda et, ex, tb: None)
        enter()
        output = None
        try:
            while True:
                line = yield output
                arglist = shlex.split(line, self.commentchar)
                try:
                    lines = self.p.parselist(arglist)
                except:
                    output = Output(None, *sys.exc_info())
                else:
                    output = Output(os.linesep.join(lines), None, None, None)
        except:
            exit(*sys.exc_info())
            raise
        else:
            exit(None, None, None)

    def check(self, given_input, expected_output, lineno=None):
        "Make sure you get the expected_output from the given_input"
        output = str(self.send(given_input))
        ok = output == expected_output
        if not ok:
            msg = 'input: %s\noutput: %s\nexpected: %s' % (
                given_input, output, expected_output)
            if lineno:
                msg = 'line %d: %s' % (lineno + 1, msg)
            raise AssertionError(msg) 

    def _parse_doctest(self, lineiter):
        lines = [line.strip() for line in lineiter]
        inputs = []
        positions = []
        for i, line in enumerate(lines):
            if line.startswith('i> '):
                inputs.append(line[3:])
                positions.append(i)
        positions.append(len(lines) + 1) # last position
        return zip(inputs, _getoutputs(lines, positions), positions)

    def doctest(self, lineiter, out=sys.stdout, verbose=False):
        """
        Parse a text containing doctests in a context and tests of all them.
        Raise an error even if a single doctest if broken. Use this for
        sequential tests which are logically grouped.
        """
        with self:
            for input, output, no in self._parse_doctest(lineiter):
                if verbose:
                    out.write('i> %s\n' % input)
                    out.write('-> %s\n' % output)
                    out.flush()
                self.check(input, output, no)

    def execute(self, lineiter, out=sys.stdout, verbose=False):
        """
        Execute a lineiter of commands in a context and print the output.
        """
        with self:
            for line in lineiter:
                if verbose:
                    out.write('i> ' + line); out.flush()
                output = self.send(line)
                if output.str is None: # there was an error
                    raise output.etype, output.exc, output.tb
                out.write('%s\n' % output.str)
                out.flush()

    def interact(self, prompt='i> ', intro=None, verbose=False):
        """Starts an interactive command loop reading commands from the
        consolle. Using rlwrap is recommended."""
        if intro is None:
            self.p.print_usage()
        else:
            print(intro)
        with self:
            while True:
                try:
                    line = raw_input(prompt)
                except EOFError:
                    break
                out = self.send(line)
                if verbose:
                    traceback.print_tb(out.tb)
                print(out)
