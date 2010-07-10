# this module requires Python 2.5+
from __future__ import with_statement
from contextlib import contextmanager
from operator import attrgetter
from gettext import gettext as _
import imp, inspect, os, sys, cmd, shlex, subprocess
import itertools, traceback, time, select, multiprocessing, signal, threading
import plac_core
try:
    import readline
except ImportError:
    readline = None

############################# generic utils ################################

@contextmanager
def stdout(fileobj):
    orig_stdout = sys.stdout
    sys.stdout = fileobj
    try:
        yield
    finally:
        sys.stdout = orig_stdout

def write(x):
    "Write str(x) on stdout and flush, no newline added"
    sys.stdout.write(str(x))
    sys.stdout.flush()

def gen_val(value):
    "Return a generator object with a single element"
    yield value

def gen_exc(etype, exc, tb):
    "Return a generator object raising an exception"
    raise etype, exc, tb
    yield

def less(text):
    "Send a text to less via a pipe"
    # -c clear the screen before starting less
    po = subprocess.Popen(['less', '-c'], stdin=subprocess.PIPE)
    try:
        po.stdin.write(text)
    except IOError:
        pass
    po.stdin.close()
    po.wait()

use_less = (sys.platform != 'win32') # unices

class TerminatedProcess(Exception):
    pass

def terminatedProcess(signum, frame):
    raise TerminatedProcess

def namedpipe(fname):
    "Return a line iterator reading from a named pipe every twice per second"
    try:
        os.mkfifo(fname)
    except OSError: # already there
        pass
    with open(fname) as fifo:
        while True:
            line = fifo.readline()
            if line == 'EOF\n':
                break
            elif line:
                yield line
            time.sleep(.5)
    os.remove(fname)

########################### readline support #############################

class ReadlineInput(object):
    """
    An iterable with a .readline method reading from stdin with readline
    features enabled, if possible. Otherwise return sys.stdin itself.
    """
    def __init__(self, completions, prompt='', case_sensitive=True,
                 histfile=None):
        self.completions = completions
        self.case_sensitive = case_sensitive
        self.histfile = histfile
        self.prompt = prompt
        if not case_sensitive:
            self.completions = map(str.upper, completions)
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)

    def __enter__(self):
        try:
            if self.histfile:
                readline.read_history_file(self.histfile)
        except IOError: # the first time
            pass
        return self

    def __exit__(self, etype, exc, tb):
        if self.histfile:
            readline.write_history_file(self.histfile)

    def complete(self, kw, state):
        # state is 0, 1, 2, ... and increases by hitting TAB
        if not self.case_sensitive:
            kw = kw.upper()
        try:
            return [k for k in self.completions if k.startswith(kw)][state]
        except IndexError: # no completions
            return # exit

    def readline(self):
        try:
            return raw_input(self.prompt) + '\n'
        except EOFError:
            return ''

    def __iter__(self):
        return iter(self.readline, '')

########################### import management ################################

try:
    PLACDIRS = os.environ.get('PLACPATH', '.').split(':')
except:
    raise ValueError(_('Ill-formed PLACPATH: got %PLACPATHs') % os.environ)

def import_main(path, *args, **pconf):
    """
    An utility to import the main function of a plac tool. It also
    works with tool factories, if you pass the arguments.
    """
    if not os.path.isabs(path): # relative path, look at PLACDIRS
        for placdir in PLACDIRS:
            fullpath = os.path.join(placdir, path)
            if os.path.exists(fullpath):
                break
        else: # no break
            raise ImportError(_('Cannot find %s'), path)
    else:
        fullpath = path
    name, ext = os.path.splitext(os.path.basename(fullpath))
    main = imp.load_module(name, open(fullpath), fullpath, (ext, 'U', 1)).main
    if args:
        cmd, tool = plac_core.parser_from(main).consume(args)
    else:
        tool = main
    # set the parser configuration and possibly raise a TypeError early
    plac_core.parser_from(tool, **pconf) 
    return tool

############################## Task classes ##############################

# base class not instantiated directly
class BaseTask(object):
    """
    A task is a wrapper over a generator object with signature
    Task(no, arglist, genobj), attributes
    .no
    .arglist
    .outlist
    .str
    .etype
    .exc
    .tb
    .status
    .synchronous
    and methods .run and .kill.
    """
    STATES = ('SUBMITTED', 'RUNNING', 'TOBEKILLED',  'KILLED', 'FINISHED',
              'ABORTED')

    def __init__(self, no, arglist, genobj):
        self.no = no
        self.arglist = arglist
        self._genobj = self._wrap(genobj)
        self.str, self.etype, self.exc, self.tb = '', None, None, None
        self.status = 'SUBMITTED'
        self.outlist = []

    def _wrap(self, genobj, stringify_tb=False):
        """
        Wrap the genobj into a generator managing the exceptions,
        populating the .outlist, setting the .status and yielding None.
        stringify_tb must be True if the traceback must be sent to a process.
        """
        self.status = 'RUNNING'
        try:
            for value in genobj:
                if self.status == 'TOBEKILLED': # exit from the loop
                    raise GeneratorExit
                if value is not None: # add output
                    self.outlist.append(value)
                yield
        except (GeneratorExit, TerminatedProcess):  # soft termination
            self.status = 'KILLED'
        except: # unexpected exception
            self.etype, self.exc, tb = sys.exc_info()
            self.tb = self.traceback if stringify_tb else tb 
            self.status = 'ABORTED'
        else: # regular exit
            self.status = 'FINISHED'
        self.str = '\n'.join(map(str, self.outlist))

    def run(self):
        "Run the inner generator"
        for none in self._genobj:
            pass

    def kill(self):
        "Set a TOBEKILLED status"
        self.status  = 'TOBEKILLED'

    def wait(self):
        "Wait for the task to finish: to be overridden"

    @property
    def traceback(self):
        "Return the traceback as a (possibly empty) string"
        if self.tb is None:
            return ''
        elif isinstance(self.tb, basestring):
            return self.tb
        else:
            return ''.join(traceback.format_tb(self.tb))

    def __str__(self):
        "String representation containing class name, number, arglist, status"
        return '<%s %d [%s] %s>' % (
            self.__class__.__name__, self.no, 
            ' '.join(self.arglist), self.status)

########################## synchronous tasks ###############################

class Outlist(object):
    "A list wrapper displaying each appended value on stdout"
    def __init__(self):
        self._ls = []
    def append(self, value):
        self._ls.append(value)
        print(value)
    def __iter__(self):
        return iter(self._ls)
    def __len__(self):
        return len(self._ls)

class SynTask(BaseTask):
    """
    Synchronous task running in the interpreter loop and displaying its
    output as soon as available.
    """
    synchronous = True

    def __init__(self, no, arglist, genobj):
        BaseTask.__init__(self, no, arglist, genobj)
        self.outlist = Outlist()
    
    def __str__(self):
        "Return the output string or the error message"
        if self.etype: # there was an error
            return '%s: %s' % (self.etype.__name__, self.exc)
        else:
            return self.str

class ThreadedTask(BaseTask):
    """
    A task running in a separated thread.
    """
    synchronous = False

    def __init__(self, no, arglist, genobj):
        BaseTask.__init__(self, no, arglist, genobj)
        self.thread = threading.Thread(target=super(ThreadedTask, self).run)

    def run(self):
        "Run the task into a thread"
        self.thread.start()

    def wait(self):
        "Block until the thread ends"
        self.thread.join()

######################### multiprocessing tasks ##########################

def sharedattr(name):
    "Return a property to be attached to an object with a .ns attribute"
    def get(self):
        return getattr(self.ns, name)
    def set(self, value):
        setattr(self.ns, name, value)
    return property(get, set)

class MPTask(BaseTask):
    """
    A task running as an external process. The current implementation
    only works on Unix-like systems, where multiprocessing use forks.
    """

    synchronous = False
    _mp_manager = None

    str = sharedattr('str')
    etype = sharedattr('etype')
    exc = sharedattr('exc')
    tb = sharedattr('tb')
    status = sharedattr('status')

    def __init__(self, no, arglist, genobj):
        if self.__class__._mp_manager is None: # the first time
            self.__class__._mp_manager = multiprocessing.Manager()
        self.no = no
        self.arglist = arglist
        self.outlist = self._mp_manager.list()
        self.ns = self._mp_manager.Namespace()
        self.str, self.etype, self.exc, self.tb = '*', None, None, None
        self.status = 'SUBMITTED'
        self._genobj = self._wrap(genobj, stringify_tb=True)
        self.proc = multiprocessing.Process(target=super(MPTask, self).run)

    def run(self):
        "Run the task into an external process"
        self.proc.start()

    def wait(self):
        "Block until the external process ends"
        self.proc.join()

    def kill(self):
        """Kill the process with a SIGTERM inducing a TerminatedProcess
        exception in the children"""
        self.proc.terminate()

######################### Task Manager #######################

class HelpSummary(object):
    "Build the help summary consistently with the cmd module"
    @classmethod
    def make(cls, obj, specialcommands):
        c = cmd.Cmd(stdout=cls())
        c.stdout.write('\n')
        c.print_topics('special commands',
                       sorted(specialcommands), 15, 80)
        c.print_topics('custom commands',
                       sorted(obj.syncommands), 15, 80)
        c.print_topics('commands run in external processes',
                       sorted(obj.mpcommands), 15, 80)
        c.print_topics('threaded commands',
                       sorted(obj.thcommands), 15, 80)
        return c.stdout
    def __init__(self):
        self._ls = []
    def write(self, s):
        self._ls.append(s)
    def __str__(self):
        return ''.join(self._ls)

class TaskManager(object):
    """
    Store the given commands into a task registry. Provides methods to
    manage the submitted tasks.
    """
    cmdprefix = '.'
    specialcommands = set(['.help', '.last_tb'])

    def __init__(self, obj):
        self.obj = obj
        self.registry = {} # {taskno : task}
        if obj.mpcommands or obj.thcommands:
            self.specialcommands.update(['.kill', '.list', '.output'])
        self.helpsummary = HelpSummary.make(obj, self.specialcommands)
        signal.signal(signal.SIGTERM, terminatedProcess)

    def run_task(self, task):
        "Run the task and update the registry"
        if not task.arglist:
            return
        cmd = task.arglist[0]
        if cmd not in self.specialcommands:
            self.registry[task.no] = task
        task.run()

    def close(self):
        "Kill all the running tasks"
        for task in self.registry.itervalues():
            if task.status == 'RUNNING':
                task.kill()
                task.wait()

    def _get_latest(self, taskno=-1, status=None):
        "Get the latest submitted task from the registry"
        assert taskno < 0, 'You must pass a negative number'
        if status:
            tasks = [t for t in self.registry.itervalues() 
                        if t.status == status]
        else:
            tasks = [t for t in self.registry.itervalues()]
        tasks.sort(key=attrgetter('no'))
        if len(tasks) >= abs(taskno):
            return tasks[taskno]

    ########################### special commands #########################

    @plac_core.annotations(
        taskno=('task to kill', 'positional', None, int))
    def kill(self, taskno=-1):
        'kill the given task (-1 to kill the latest running task)'
        if taskno < 0:
            task = self._get_latest(taskno, status='RUNNING')
            if task is None:
                yield 'Nothing to kill'
                return
        elif not taskno in self.registry:
            yield 'Unknown task %d' % taskno
            return
        else:
            task = self.registry[taskno]
        if task.status in ('ABORTED', 'KILLED', 'FINISHED'):
            yield 'Already finished %s' % task
            return
        task.kill()
        yield task

    @plac_core.annotations(
        status=('', 'positional', None, str, BaseTask.STATES))
    def list(self, status='RUNNING'):
        'list tasks with a given status'
        for task in self.registry.values():
            if task.status == status:
                yield task

    @plac_core.annotations(
        taskno=('task number', 'positional', None, int))
    def output(self, taskno=-1):
        'show the output of a given task'
        if taskno < 0:
            task = self._get_latest(taskno)
            if task is None:
                yield 'Nothing to show'
                return
        elif taskno not in self.registry:
            yield 'Unknown task %d' % taskno
            return
        else:
            task = self.registry[taskno]
        outstr = '\n'.join(task.outlist)
        yield task
        if len(task.outlist) > 20 and use_less:
            less(outstr)
        else:
            yield outstr

    @plac_core.annotations(
        taskno=('task number', 'positional', None, int))
    def last_tb(self, taskno=-1):
        "show the traceback of a given task, if any"
        task = self._get_latest(taskno)
        if task:
            yield task.traceback
        else:
            yield 'Nothing to show'

    def help(self, cmd=None):
        "show help about a given command"
        if cmd is None:
            yield str(self.helpsummary)
        else:
            yield plac_core.parser_from(self.obj).help_cmd(cmd)

########################### SyncProcess ##############################

class Process(subprocess.Popen):
    "Start the interpreter specified by the params in a subprocess"

    def __init__(self, params):
        code = '''import plac
plac.Interpreter(plac.import_main(*%s)).interact(prompt='i>\\n')
''' % params
        subprocess.Popen.__init__(
            self, [sys.executable, '-u', '-c', code],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def close(self):
        "Close stdin and stdout"
        self.stdin.close()
        self.stdout.close()

    def recv(self): # char-by-char cannot work
        "Return the output of the subprocess, line-by-line until the prompt"
        lines = []
        while True:
            lines.append(self.stdout.readline())
            if lines[-1] == 'i>\n':
                out = ''.join(lines)
                return out[:-1] + ' ' # remove last newline

    def send(self, line):
        """Send a line (adding a newline) to the underlying subprocess 
        and wait for the answer"""
        self.stdin.write(line + os.linesep)
        return self.recv()

########################### the Interpreter #############################

class Interpreter(object):
    """
    A context manager with a .send method and a few utility methods:
    execute, test and doctest.
    """
    def __init__(self, obj, commentchar='#'):
        self.obj = obj
        try:
            self.name = obj.__module__
        except AttributeError:
            self.name = 'plac'
        self.commentchar = commentchar
        self._set_commands(obj)
        self.tm = TaskManager(obj)
        self.parser = plac_core.parser_from(obj, prog='', add_help=False)
        if self.commands:
            self.commands.update(self.tm.specialcommands)
            self.parser.addsubcommands(self.tm.specialcommands, self.tm,
                                  title='special commands')
        if obj.mpcommands:
            self.parser.addsubcommands(obj.mpcommands, obj,
                                  title='commands run in external processes')
        if obj.thcommands:
            self.parser.addsubcommands(obj.thcommands, obj,
                                  title='threaded commands')
        self.parser.error = lambda msg: sys.exit(msg) # patch the parser
        self._interpreter = None

    def _set_commands(self, obj):
        "Make sure obj has the right command attributes as Python sets"
        for attrname in ('commands', 'syncommands', 'mpcommands', 'thcommands'):
            try:
                sequence = getattr(obj, attrname)
            except AttributeError:
                sequence = []
            if not isinstance(sequence, set):
                sequence = set(sequence)
            setattr(obj, attrname, sequence)
        obj.syncommands.update(obj.commands)
        self.commands = obj.commands
        self.commands.update(obj.syncommands)
        self.commands.update(obj.mpcommands)
        self.commands.update(obj.thcommands)

    def __enter__(self):
        self._interpreter = self._make_interpreter()
        self._interpreter.send(None)
        return self

    def __exit__(self, *exc):
        self.close()

    def make_task(self, line):
        "Send a line to the underlying interpreter and return a task object"
        if self._interpreter is None:
            raise RuntimeError(_('%r not initialized: probably you forgot to '
                                 'use the with statement') % self)
        if isinstance(line, basestring):
            arglist = shlex.split(line, self.commentchar)
        else: # expects a list of strings
            arglist = line
        return self._interpreter.send(arglist)
        
    def send(self, line):
        "Send a line to the underlying interpreter and return the result"
        task = self.make_task(line)
        BaseTask.run(task) # blocking
        return task

    def close(self):
        "Can be called to close the interpreter prematurely"
        self.tm.close()
        self._interpreter.close()

    def _make_interpreter(self):
        "The interpreter main loop, from lists of arguments to task objects"
        enter = getattr(self.obj, '__enter__', lambda : None)
        exit = getattr(self.obj, '__exit__', lambda et, ex, tb: None)
        enter()
        task = None
        try:
            for no in itertools.count(1):
                arglist = yield task
                try:
                    cmd, result = self.parser.consume(arglist)
                except: # i.e. SystemExit for invalid command
                    task = SynTask(no, arglist, gen_exc(*sys.exc_info()))
                    continue
                if not plac_core.iterable(result): # atomic result
                    task = SynTask(no, arglist, gen_val(result))
                elif cmd in self.obj.mpcommands:
                    task = MPTask(no, arglist, result)
                elif cmd in self.obj.thcommands:
                    task = ThreadedTask(no, arglist, result)
                else: # blocking task
                    task = SynTask(no, arglist, result)
        except GeneratorExit: # regular exit
            exit(None, None, None)
        except: # exceptional exit
            exit(*sys.exc_info())
            raise

    def check(self, given_input, expected_output):
        "Make sure you get the expected_output from the given_input"
        output = self.send(given_input).str # blocking
        ok = (output == expected_output)
        if not ok:
            # the message here is not internationalized on purpose
            msg = 'input: %s\noutput: %s\nexpected: %s' % (
                given_input, output, expected_output)
            raise AssertionError(msg) 

    def _getoutputs(self, lines, intlist):
        "helper used in parse_doctest"
        for i, start in enumerate(intlist[:-1]):
            end = intlist[i + 1]
            yield '\n'.join(lines[start+1:end])

    def _parse_doctest(self, lineiter):
        lines = [line.strip() for line in lineiter]
        inputs = []
        positions = []
        for i, line in enumerate(lines):
            if line.startswith('i> '):
                inputs.append(line[3:])
                positions.append(i)
        positions.append(len(lines) + 1) # last position
        return zip(inputs, self._getoutputs(lines, positions), positions)

    def doctest(self, lineiter, verbose=False):
        """
        Parse a text containing doctests in a context and tests of all them.
        Raise an error even if a single doctest if broken. Use this for
        sequential tests which are logically grouped.
        """
        with self:
            for input, output, no in self._parse_doctest(lineiter):
                if verbose:
                    write('i> %s\n' % input)
                    write('-> %s\n' % output)
                task = self.send(input) # blocking
                if not str(task) == output:
                    msg = 'line %d: input: %s\noutput: %s\nexpected: %s\n' % (
                        no + 1, input, task, output)
                    write(msg)
                    raise task.etype, task.exc, task.tb

    def execute(self, lineiter, verbose=False):
        """
        Execute a lineiter of commands in a context and print the output.
        """
        with self:
            for line in lineiter:
                if verbose:
                    write('i> ' + line)
                task = self.send(line) # finished task
                if task.etype: # there was an error
                    raise task.etype, task.exc, task.tb
                if not task.synchronous:
                    write('%s\n' % task.str)

    def interact(self, stdin=sys.stdin, prompt='i> ', verbose=False):
        """
        Starts an interactive command loop reading commands from the
        consolle. Using rlwrap is recommended.
        """
        if stdin is sys.stdin and readline: # use readline
            # print '.%s.history' % self.name
            stdin = ReadlineInput(
                self.commands, prompt, histfile='.%s.history' % self.name,
                case_sensitive=True)
        self.stdin = stdin
        self.prompt = getattr(stdin, 'prompt', prompt)
        self.verbose = verbose
        intro = self.obj.__doc__ or ''
        write(intro + '\n')
        with self:
            if self.stdin is sys.stdin: # do not close stdin automatically
                self._manage_input()
            else:
                with self.stdin:
                    self._manage_input()

    def _manage_input(self):
        while True: # using 'for' would not work well with unbuffered mode
            if not isinstance(self.stdin, ReadlineInput):
                write(self.prompt) # else the prompt is already there
            line = self.stdin.readline() # including \n
            if not line:
                break
            task = self.make_task(line)
            self.tm.run_task(task)
            if self.verbose and task.synchronous and task.etype:
                write(task.traceback)
            if task.etype or not task.synchronous:
                write(str(task) + '\n')
