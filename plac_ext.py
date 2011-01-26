# this module requires Python 2.5+
from __future__ import with_statement
from contextlib import contextmanager
from operator import attrgetter
from gettext import gettext as _
import imp, inspect, os, sys, cmd, shlex, subprocess
import itertools, traceback, multiprocessing, signal, threading
import plac_core

############################# generic utils ################################

@contextmanager
def stdout(fileobj):
    "usage: with stdout(file('out.txt', 'a')): do_something()"
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

########################### readline support #############################

def read_line(stdin, prompt=''):
    "Read a line from stdin, using readline when possible"
    if isinstance(stdin, ReadlineInput):
        return stdin.readline(prompt)
    else:
        write(prompt)
        return stdin.readline()

def read_long_line(stdin, terminator):
    """
    Read multiple lines from stdin until the terminator character is found, then
    yield a single space-separated long line.
    """
    while True:
        lines = []
        while True:
            line = stdin.readline() # ends with \n
            if not line: # EOF
                return
            line = line.strip()
            if not line:
                continue
            elif line[-1] == terminator:
                lines.append(line[:-1])
                break
            else:
                lines.append(line)
        yield ' '.join(lines)

class ReadlineInput(object):
    """
    An iterable with a .readline method reading from stdin.
    """
    def __init__(self, completions, case_sensitive=True, histfile=None):
        self.completions = completions
        self.case_sensitive = case_sensitive
        self.histfile = histfile
        if not case_sensitive:
            self.completions = map(str.upper, completions)
        import readline
        self.rl = readline
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.complete)

    def __enter__(self):
        self.old_completer = self.rl.get_completer()
        try:
            if self.histfile:
                self.rl.read_history_file(self.histfile)
        except IOError: # the first time
            pass
        return self

    def __exit__(self, etype, exc, tb):
        self.rl.set_completer(self.old_completer)
        if self.histfile:
            self.rl.write_history_file(self.histfile)

    def complete(self, kw, state):
        # state is 0, 1, 2, ... and increases by hitting TAB
        if not self.case_sensitive:
            kw = kw.upper()
        try:
            return [k for k in self.completions if k.startswith(kw)][state]
        except IndexError: # no completions
            return # exit

    def readline(self, prompt=''):
        try:
            return raw_input(prompt) + '\n'
        except EOFError:
            return ''

    def __iter__(self):
        return iter(self.readline, '')

########################### import management ################################

try:
    PLACDIRS = os.environ.get('PLACPATH', '.').split(':')
except:
    raise ValueError(_('Ill-formed PLACPATH: got %PLACPATHs') % os.environ)

def partial_call(factory, arglist):
    "Call a container factory with the arglist and return a plac object"

    a = plac_core.parser_from(factory).argspec
    if a.defaults or a.varargs or a.varkw:
        raise TypeError('Interpreter.call must be invoked on '
                        'factories with required arguments only')
    required_args = ', '.join(a.args)
    if required_args:
        required_args += ',' # trailing comma
    code = '''def makeobj(interact, %s *args):
    obj = factory(%s)
    obj._interact_ = interact
    obj._args_ = args
    return obj\n'''% (required_args, required_args)
    dic = dict(factory=factory)
    exec code in dic
    makeobj = dic['makeobj']
    if inspect.isclass(factory):
        makeobj.__annotations__ = getattr(
            factory.__init__, '__annotations__', {})
    else:
        makeobj.__annotations__ = getattr(
            factory, '__annotations__', {})
    makeobj.__annotations__['interact'] = (
        'start interactive interpreter', 'flag', 'i')
    return plac_core.call(makeobj, arglist)

def import_main(path, *args, **pconf):
    """
    An utility to import the main function of a plac tool. It also
    works with command container factories.
    """
    if ':' in path: # importing a factory
        path, factory_name = path.split(':')
    else: # importing the main function
        factory_name = None
    if not os.path.isabs(path): # relative path, look at PLACDIRS
        for placdir in PLACDIRS:
            fullpath = os.path.join(placdir, path)
            if os.path.exists(fullpath):
                break
        else: # no break
            raise ImportError(_('Cannot find %s' % path))
    else:
        fullpath = path
    name, ext = os.path.splitext(os.path.basename(fullpath))
    module = imp.load_module(name, open(fullpath), fullpath, (ext, 'U', 1))
    if factory_name:
        tool = partial_call(getattr(module, factory_name), args)
    else:
        tool = module.main
    # set the parser configuration
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

    def notify(self, msg):
        "Notifies the underlying monitor. To be implemented"

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
                    self.notify(str(value))
                yield
        except (GeneratorExit, TerminatedProcess, KeyboardInterrupt): 
            # soft termination
            self.status = 'KILLED'
        except: # unexpected exception
            self.etype, self.exc, tb = sys.exc_info()
            self.tb = ''.join(traceback.format_tb(tb)) if stringify_tb else tb
            self.status = 'ABORTED'
        else: # regular exit
            self.status = 'FINISHED'
            try:
                self.str = '\n'.join(map(str, self.outlist))
            except IndexError:
                self.str = 'no result'

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

    @property
    def result(self):
        self.wait()
        if self.exc:
            raise self.etype, self.exc, self.tb or None
        if not self.outlist:
            return None
        return self.outlist[-1]

    def __repr__(self):
        "String representation containing class name, number, arglist, status"
        return '<%s %d [%s] %s>' % (
            self.__class__.__name__, self.no, 
            ' '.join(self.arglist), self.status)

nulltask = BaseTask(0, [], ('skip' for dummy in (1,)))

########################## synchronous tasks ###############################

class SynTask(BaseTask):
    """
    Synchronous task running in the interpreter loop and displaying its
    output as soon as available.
    """    
    def __str__(self):
        "Return the output string or the error message"
        if self.etype: # there was an error
            return '%s: %s' % (self.etype.__name__, self.exc)
        else:
            return '\n'.join(map(str, self.outlist))

class ThreadedTask(BaseTask):
    """
    A task running in a separated thread.
    """
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

def sharedattr(name, on_error):
    "Return a property to be attached to an MPTask"
    def get(self):
        try:
            return getattr(self.ns, name)
        except: # the process was killed or died hard
            return on_error
    def set(self, value):
        try:
            setattr(self.ns, name, value)
        except: # the process was killed or died hard
            pass
    return property(get, set)

class MPTask(BaseTask):
    """
    A task running as an external process. The current implementation
    only works on Unix-like systems, where multiprocessing use forks.
    """
    str = sharedattr('str', '')
    etype = sharedattr('etype', None)
    exc = sharedattr('exc', None)
    tb = sharedattr('tb', None)
    status = sharedattr('status', 'ABORTED')

    @property
    def outlist(self):
        try:
            return self._outlist
        except: # the process died hard
            return []

    def notify(self, msg):
        self.man.send('notify_listener %d %r' % (self.no, msg))

    def __init__(self, no, arglist, genobj, manager):
        """
        The monitor has a .send method and a .man multiprocessing.Manager
        """
        self.no = no
        self.arglist = arglist
        self._genobj = self._wrap(genobj, stringify_tb=True)
        self.man = manager
        self._outlist = manager.mp.list()
        self.ns = manager.mp.Namespace()
        self.status = 'SUBMITTED'
        self.etype, self.exc, self.tb = None, None, None
        self.str = repr(self)
        self.proc = multiprocessing.Process(target=super(MPTask, self).run)

    def run(self):
        "Run the task into an external process"
        self.proc.start()

    def wait(self):
        "Block until the external process ends or is killed"
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
        self.man = Manager() if obj.mpcommands else None
        signal.signal(signal.SIGTERM, terminatedProcess)

    def close(self):
        "Kill all the running tasks"
        for task in self.registry.itervalues():
            try:
                if task.status == 'RUNNING':
                    task.kill()
                    task.wait()
            except: # task killed, nothing to wait
                pass
        if self.man:
            self.man.stop()

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
    def output(self, taskno=-1, fname=None):
        'show the output of a given task (and optionally save it to a file)'
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
        outstr = '\n'.join(map(str, task.outlist))
        if fname:
            open(fname, 'w').write(outstr)
            yield 'saved output of %d into %s' % (taskno, fname); return
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
        signal.signal(signal.SIGPIPE, signal.SIG_DFL) 
        # to avoid broken pipe messages
        code = '''import plac, sys
sys.argv[0] = '<%s>'
plac.Interpreter(plac.import_main(*%s)).interact(prompt='i>\\n')
''' % (params[0], params)
        subprocess.Popen.__init__(
            self, [sys.executable, '-u', '-c', code],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.man = multiprocessing.Manager()

    def close(self):
        "Close stdin and stdout"
        self.stdin.close()
        self.stdout.close()
        self.man.shutdown()

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

class Monitor(object):
    """
    Base monitor class with methods add_listener/del_listener/notify_listener
    and start/stop/schedule/slave.
    """
    commands = 'add_listener', 'del_listener', 'notify_listener'
    def __init__(self, name):
        self.name = name
    def add_listener(self, taskno):
        pass
    def del_listener(self, taskno):
        pass    
    def notify_listener(self, taskno, msg):
        pass
    def start(self):
        pass
    def stop(self):
        pass
    def schedule(self, seconds, display, arg):
        pass

import Queue

class SlaveProcess(object):
    """
    Spawn a slave process reading from an input queue and displaying
    on a monitor object. Methods are start/send/stop.
    """
    def __init__(self, mon):
        self.mon= mon
        self.queue = multiprocessing.Queue()
        self.proc = multiprocessing.Process(None, self._run)

    def start(self):
        self.proc.start()

    def send(self, line):
        self.queue.put(line)

    def stop(self):
        self.queue.close()
        self.proc.terminate()

    def _sendline(self, i):
        "Send a line to the underlying monitor"
        try:
            line = self.queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            i.send(line)
        self.mon.schedule(.1, self._sendline, i)

    def _run(self):
        with Interpreter(self.mon) as i:
            # .schedule() must be invoked inside the with block
            self.mon.schedule(.1, self._sendline, i)
            self.mon.run()

class StartStopObject(object):
    started = False
    def start(self): pass
    def stop(self): pass

class Manager(StartStopObject):
    """
    The plac Manager contains a multiprocessing.Manager and a set
    of slave monitor processes to which we can send commands. There
    is a manager for each interpreter with mpcommands.
    """
    def add(self, monitor):
        'Add or replace a monitor in the registry'
        slave = SlaveProcess(monitor)
        name = slave.name = monitor.name
        self.registry[name] = slave

    def delete(self, name):
        'Remove a named monitor from the registry'
        del self.registry[name]

    def __init__(self):
        self.registry = {}
        self.started = False
        self.mp = None

    # can be called more than once
    def start(self):
        if self.mp is None:
            self.mp = multiprocessing.Manager()
        for slave in self.registry.itervalues():
            slave.start()
        self.started = True

    def stop(self):
        for slave in self.registry.itervalues():
            slave.stop()
        if self.mp:
            self.mp.shutdown()
            self.mp = None
        self.started = False

    def send(self, line):
        for slave in self.registry.itervalues():
            slave.send(line)

########################## plac server ##############################

import asyncore, asynchat, socket

class _AsynHandler(asynchat.async_chat):
    "asynchat handler starting a new interpreter loop for each connection"

    terminator = '\r\n' # the standard one for telnet
    prompt = 'i> '

    def __init__(self, socket, interpreter):
        asynchat.async_chat.__init__(self, socket)
        self.set_terminator(self.terminator)
        self.i = interpreter
        self.i.__enter__()
        self.data = []
        self.write(self.prompt)

    def write(self, data, *args):
        "Push a string back to the client"
        if args:
            data %= args
        if data.endswith('\n') and not data.endswith(self.terminator):
            data = data[:-1] + self.terminator # fix newlines
        self.push(data)
    
    def collect_incoming_data(self, data):
        "Collect one character at the time"
        self.data.append(data)

    def found_terminator(self):
        "Put in the queue the line received from the client"
        line = ''.join(self.data)
        self.log('Received line %r from %s' % (line, self.addr))
        if line == 'EOF':
            self.i.__exit__()
            self.handle_close()
        else:
            task = self.i.submit(line)
            task.run() # synchronous or not
            if task.etype: # manage exception
                error = '%s: %s\nReceived: %s' % (
                    task.etype.__name__, task.exc, ' '.join(task.arglist))
                self.log_info(task.traceback + error) # on the server
                self.write(error + self.terminator) # back to the client
            else: # no exception
                self.write(task.str + self.terminator)
            self.data = []
            self.write(self.prompt)

class _AsynServer(asyncore.dispatcher):
    "asyncore-based server spawning AsynHandlers"

    def __init__(self, interpreter, newhandler, port, listen=5):
        self.interpreter = interpreter
        self.newhandler = newhandler
        self.port = port
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', port))
        self.listen(listen)

    def handle_accept(self):
        clientsock, clientaddr = self.accept()
        self.log('Connected from %s' % str(clientaddr))
        i = self.interpreter.__class__(self.interpreter.obj) # new interpreter
        self.newhandler(clientsock, i) # spawn a new handler

########################### the Interpreter #############################

class Interpreter(object):
    """
    A context manager with a .send method and a few utility methods:
    execute, test and doctest.
    """
    def __init__(self, obj, commentchar='#', split=shlex.split):
        self.obj = obj
        try:
            self.name = obj.__module__
        except AttributeError:
            self.name = 'plac'
        self.commentchar = commentchar
        self.split = split
        self._set_commands(obj)
        self.tm = TaskManager(obj)
        self.man = self.tm.man
        self.parser = plac_core.parser_from(obj, prog='', add_help=False)
        if self.commands:
            self.commands.update(self.tm.specialcommands)
            self.parser.addsubcommands(
                self.tm.specialcommands, self.tm, title='special commands')
        if obj.mpcommands:
            self.parser.addsubcommands(
                obj.mpcommands, obj, title='commands run in external processes')
        if obj.thcommands:
            self.parser.addsubcommands(
                obj.thcommands, obj, title='threaded commands')
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
        "Start the inner interpreter loop"
        self._interpreter = self._make_interpreter()
        self._interpreter.send(None)
        return self

    def __exit__(self, exctype, exc, tb):
        "Close the inner interpreter and the task manager"
        self.close(exctype, exc, tb)

    def submit(self, line):
        "Send a line to the underlying interpreter and return a task object"
        if self._interpreter is None:
            raise RuntimeError(_('%r not initialized: probably you forgot to '
                                 'use the with statement') % self)
        if isinstance(line, basestring):
            arglist = self.split(line, self.commentchar)
        else: # expects a list of strings
            arglist = line
        if not arglist:
            return nulltask
        m = self.tm.man # manager
        if m and not m.started:
            m.start()
        task = self._interpreter.send(arglist) # nonblocking
        if not plac_core._match_cmd(arglist[0], self.tm.specialcommands):
            self.tm.registry[task.no] = task
            if m:
                m.send('add_listener %d' % task.no)
        return task

    def send(self, line):
        "Send a line to the underlying interpreter and return the finished task"
        task = self.submit(line)
        BaseTask.run(task) # blocking
        return task

    def tasks(self):
        "The full lists of the submitted tasks"
        return self.tm.registry.values()

    def close(self, exctype=None, exc=None, tb=None):
        "Can be called to close the interpreter prematurely"
        self.tm.close()
        if exctype is not None:
            self._interpreter.throw(exctype, exc, tb)
        else:
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
                    task = MPTask(no, arglist, result, self.tm.man)
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

    def _parse_doctest(self, lineiter):
        "Returns the lines of input, the lines of output, and the line number"
        lines = [line.strip() for line in lineiter]
        inputs = []
        positions = []
        for i, line in enumerate(lines):
            if line.startswith('i> '):
                inputs.append(line[3:])
                positions.append(i)
        positions.append(len(lines) + 1) # last position
        outputs = []
        for i, start in enumerate(positions[:-1]):
            end = positions[i + 1]
            outputs.append('\n'.join(lines[start+1:end]))
        return zip(inputs, outputs, positions)

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
        "Execute a lineiter of commands in a context and print the output"
        with self:
            for line in lineiter:
                if verbose:
                    write('i> ' + line)
                task = self.send(line) # finished task
                if task.etype: # there was an error
                    raise task.etype, task.exc, task.tb
                write('%s\n' % task.str)

    def multiline(self, stdin=sys.stdin, terminator=';', verbose=False):
        "The multiline mode is especially suited for usage with emacs"
        with self:
            for line in read_long_line(stdin, terminator):
                task = self.submit(line)
                task.run()
                write('%s\n' % task.str)
                if verbose and task.traceback:
                    write(task.traceback)

    def interact(self, stdin=sys.stdin, prompt='i> ', verbose=False):
        "Starts an interactive command loop reading commands from the consolle"
        try:
            import readline
            readline_present = True
        except ImportError:
            readline_present = False
        if stdin is sys.stdin and readline_present: # use readline
            histfile = os.path.expanduser('~/.%s.history' % self.name)
            self.stdin = ReadlineInput(self.commands, histfile=histfile)
        else:
            self.stdin = stdin
        self.prompt = prompt
        self.verbose = verbose
        intro = self.obj.__doc__ or ''
        write(intro + '\n')
        with self:
            if self.stdin is sys.stdin: # do not close stdin automatically
                self._manage_input()
            else:
                with self.stdin: # close stdin automatically
                    self._manage_input()

    def _manage_input(self):
        "Convert input lines into task which are then executed"
        for line in iter(lambda : read_line(self.stdin, self.prompt), ''):
            line = line.strip()
            if not line:
                continue
            task = self.submit(line)
            task.run() # synchronous or not
            write(str(task) + '\n')
            if self.verbose and task.etype:
                write(task.traceback)

    def start_server(self, port=2199, **kw):
        """Starts an asyncore server reading commands for clients and opening
        a new interpreter for each connection."""
        _AsynServer(self, _AsynHandler, port) # register the server
        try:
            asyncore.loop(**kw)
        except KeyboardInterrupt:
            pass
        finally:
            asyncore.close_all()

    def stop_server(self, after=0.0):
        "Stops the asyncore server, possibly after a given number of seconds"
        threading.Timer(after, asyncore.socket_map.clear).start()

    def add_monitor(self, mon):
        self.man.add(mon)

    def del_monitor(self, name):
        self.man.delete(name)

    @classmethod
    def call(cls, factory, arglist=sys.argv[1:], 
             commentchar='#', split=shlex.split, 
             stdin=sys.stdin, prompt='i> ', verbose=False):
        """
        Call a container factory with the arglist and instantiate an
        interpreter object. If there are remaining arguments, send them to the
        interpreter, else start an interactive session.
        """
        obj = partial_call(factory, arglist)
        i = cls(obj, commentchar, split)
        if i.obj._args_:
            with i:
                task = i.send(i.obj._args_) # synchronous
                if task.exc:
                    raise task.etype, task.exc, task.tb
                print(task)
        elif i.obj._interact_:
            i.interact(stdin, prompt, verbose)
        else:
            i.parser.print_usage()

#################################### runp #####################################

class _TaskLauncher(object):
    "Helper for runp"

    def __init__(self, genseq, mode):
        if mode == 'p':
            self.mpcommands = ['rungen']
        else:
            self.thcommands = ['rungen']
        self.genlist = list(genseq)

    def rungen(self, i):
        for out in self.genlist[int(i) - 1]:
            yield out

def runp(genseq, mode='p', monitors=(), start=True):
    """Run a sequence of generators in parallel. Mode can be 'p' (use processes)
    or 't' (use threads). Return a list of running task objects. If start is
    False, the tasks are only submitted and not automatically started.
    """
    assert mode in 'pt', mode
    launcher = _TaskLauncher(genseq, mode)
    inter = Interpreter(launcher).__enter__()
    for mon in monitors: # must be added before submit
        inter.add_monitor(mon)
    for i in range(len(launcher.genlist)):
        inter.submit('rungen %d' % (i + 1))
    if start:
        for task in inter.tasks():
            task.run()
    return inter.tasks()
