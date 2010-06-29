# this module requires Python 2.5+
from __future__ import with_statement
from operator import attrgetter
import imp, inspect, os, sys, cmd, shlex, subprocess
import itertools, traceback, time, select, multiprocessing, signal
import plac_core

############################# generic utils ################################

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

########################### import management ################################

try:
    PLACDIRS = os.environ.get('PLACPATH', '.').split(':')
except:
    raise ValueError('Ill-formed PLACPATH: got %PLACPATHs' % os.environ)

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
            raise ImportError('Cannot find %s', path)
    else:
        fullpath = path
    name, ext = os.path.splitext(os.path.basename(fullpath))
    tool = imp.load_module(name, open(fullpath), fullpath, (ext, 'U', 1)).main
    if args:
        cmd, tool = plac_core.parser_from(tool).consume(args)
    elif inspect.isclass(tool):
        tool = tool() # instantiate it
    vars(tool).update(pconf)
    plac_core.parser_from(tool) # raise a TypeError if not
    return tool

######################## Tasks management ##########################

class TerminatedProcess(Exception):
    pass

def terminatedProcess(signum, frame):
    raise TerminatedProcess

class Task(object):
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
    STATES = 'SUBMITTED', 'RUNNING', 'FINISHED', 'ABORTED', 'KILLED'
    synchronous = True # may be overridden in subclasses

    def __init__(self, no, arglist, genobj):
        self.no = no
        self.arglist = arglist
        self._genobj = self._wrap(genobj)
        self.str, self.etype, self.exc, self.tb = '*', None, None, None
        self.status = 'SUBMITTED'
        self.outlist = []

    def _wrap(self, genobj, stringify_tb=False):
        """
        Wrap the genobj into a generator managing the exceptions,
        populating the .outlist, setting the .status and yielding None.
        """
        self.status = 'RUNNING'
        try:
            for value in genobj:
                if value is not None:
                    self.outlist.append(value)
                yield
        except (GeneratorExit, TerminatedProcess):  # soft termination
            self.status = 'KILLED'
        except: # unexpect exception
            self.etype, self.exc, tb = sys.exc_info()
            self.tb = self.traceback if stringify_tb else tb 
            # needed when sending the traceback to a process
            self.status = 'ABORTED'
        else: # regular exit
            self.status = 'FINISHED'
        self.str = '\n'.join(map(str, self.outlist))

    def run(self):
        "Run the inner generator"
        for none in self._genobj:
            pass

    def kill(self):
        "Kill softly the task by closing the inner generator"
        self._genobj.close()

    def wait(self):
        "Wait for the task to finish: overridden in MPTask"

    def __str__(self):
        "Returns the output string or the error message"
        if self.etype: # there was an error
            return '%s: %s' % (self.etype.__name__, self.exc)
        else:
            return self.str

    @property
    def traceback(self):
        if self.tb is None:
            return ''
        elif isinstance(self.tb, basestring):
            return self.tb
        else:
            return ''.join(traceback.format_tb(self.tb))

class TaskManager(object):
    specialcommands = set(['_help', '_kill', '_list', '_output', '_last_tb'])

    def __init__(self, obj):
        self.obj = obj
        self._extract_commands_from(obj)
        self.registry = {} # {taskno : task}
        signal.signal(signal.SIGTERM, terminatedProcess)

    def _extract_commands_from(self, obj):
        "Make sure self has the right command attributes"
        for attrname in ('commands', 'asyncommands', 'mpcommands'):
            try:
                sequence = getattr(obj, attrname)
            except AttributeError:
                sequence = []
            if not isinstance(sequence, set):
                sequence = set(sequence)
            setattr(self, attrname, sequence)        
        self.commands.update(self.asyncommands, self.mpcommands)
        for cmd in self.commands:
            setattr(self, cmd, getattr(obj, cmd))
        if self.commands:
            self.commands.update(self.specialcommands)
            self.add_help = False

    def run_task(self, task):
        "Run the task and update the registry"
        if not task.synchronous:
            self.registry[task.no] = task
        task.run()

    def close(self):
        "Kill all the running tasks"
        for task in self.registry.itervalues():
            if task.status == 'RUNNING':
                task.kill()
                task.wait()

    def _get_latest(self, taskno=-1, status=None, synchronous=False):
        "Get the latest submitted task from the registry"
        assert taskno < 0, 'You must pass a negative number'
        if status:
            tasks = [t for t in self.registry.itervalues() 
                        if t.status == status and t.synchronous == synchronous]
        else:
            tasks = [t for t in self.registry.itervalues()
                     if t.synchronous == synchronous]
        tasks.sort(key=attrgetter('no'))
        if len(tasks) >= abs(taskno):
            return tasks[taskno]

    ########################### special commands #########################

    @plac_core.annotations(
        taskno=('task to kill', 'positional', None, int))
    def _kill(self, taskno=-1):
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
        yield 'Killed task %s' % task

    @plac_core.annotations(
        status=('list of tasks with a given status', 'positional',
                None, str, Task.STATES))
    def _list(self, status='RUNNING'):
        'list tasks with a given status'
        for task in self.registry.values():
            if task.status == status:
                yield task

    @plac_core.annotations(
        taskno=('task number', 'positional', None, int))
    def _output(self, taskno=-1):
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

    def _last_tb(self):
        task = self._get_latest(synchronous=True)
        yield task.traceback + '\n'

    def _help(self, cmd=None):
        yield cmd_help(self.obj.asyncommands)
        #yield self.p.format_help()

######################## Process management ##########################

def sharedattr(name):
    "Return a property to be attached to an object with a .ns attribute"
    def get(self):
        return getattr(self.ns, name)
    def set(self, value):
        setattr(self.ns, name, value)
    return property(get, set)

class MPTask(Task):
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
        self.str, self.etype, self.exc, self.tb = None, None, None, None
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

    def __str__(self):
        return '<%s %d [%s] %s>' % (
            self.__class__.__name__, self.no, 
            ' '.join(self.arglist), self.status)

class SyncProcess(subprocess.Popen):
    "Start the interpreter specified by the params in a subprocess"

    def __init__(self, params):
        code = '''import plac
plac.Interpreter(plac.import_main(*%s), prompt='i>\\n').interact()
''' % params
        subprocess.Popen.__init__(
            self, [sys.executable, '-u', '-c', code],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def close(self):
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
        "Send a line (adding a newline) to the subprocess"
        self.stdin.write(line + os.linesep)
        return self.recv()

############################# asynchronous utilities #########################
 
# eventloop inspired to monocle (http://github.com/saucelabs/monocle)
class EventLoop(object):
    """
    A trivial event loop with a monocle-consistent interface, i.e. methods
    queue_task, run and halt.
    """
    def __init__(self):
        self._running = True
        self._queue = []

    def queue_task(self, delay, callable, *args, **kw):
        when = time.time() + delay
        self._queue.append((when, callable, args, kw))
        self._queue.sort(reverse=True) # the last is the most recent

    def run(self):
        while self._running:
            if self._queue: # there is always the select in queue
                when = self._queue[-1][0] 
                if when <= time.time():
                    task = self._queue.pop()
                    task[1](*task[2], **task[3])
            time.sleep(0.05)

    def halt(self):
        self._running = False

class AsynTask(Task):
    "Lightweight wrapper over a generator running into an event loop"

    synchronous = False
    eventloop = EventLoop()
    delay = 0

    def run(self):
        "Run the asyntask inside an eventloop"
        eventloop = self.eventloop
        delay = self.delay
        def next_and_reschedule(): # unless stop iteration
            try:
                self._genobj.next()
            except StopIteration: # error management inside _wrap
                return
            eventloop.queue_task(delay, next_and_reschedule)
        eventloop.queue_task(delay, next_and_reschedule)

    def __str__(self):
        return '<%s %d [%s] %s>' % (
            self.__class__.__name__, self.no, 
            ' '.join(self.arglist), self.status)

########################### the Interpreter #############################

class Interpreter(object):
    """
    A context manager with a .send method and a few utility methods:
    execute, test and doctest.
    """
    counter = itertools.count(1)

    def __init__(self, obj, commentchar='#', prompt='i> ', 
                 loop=AsynTask.eventloop):
        self.obj = obj
        self.commentchar = commentchar
        self.prompt = prompt
        self.eventloop = loop       
        self.tm = TaskManager(obj)
        try:
            self.p = plac_core.parser_from(obj)
        except TypeError: # obj is not callable
            self.p = plac_core.parser_from(self.tm)
        self.p.error = lambda msg: sys.exit(msg) # patch the parser
        self._interpreter = None

    def __enter__(self):
        self._interpreter = self._make_interpreter()
        self._interpreter.send(None)
        return self

    def maketask(self, line):
        "Send a line to the underlying interpreter and return a task object"
        if self._interpreter is None:
            raise RuntimeError('%r not initialized: probably you forgot to '
                               'use the with statement' % self)
        if isinstance(line, basestring):
            arglist = shlex.split(line, self.commentchar)
        else:
            arglist = line
        return self._interpreter.send(arglist)
        
    def send(self, line):
        "Send a line to the underlying interpreter and return the result"
        task = self.maketask(line)
        Task.run(task) # blocking
        return task

    def close(self):
        "Can be called to close the interpreter prematurely"
        self.tm.close()
        self._interpreter.close()

    def __exit__(self, *exc):
        self.close()

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
                    cmd, result = self.p.consume(arglist)
                except: # i.e. SystemExit for invalid command
                    task = Task(no, arglist, gen_exc(*sys.exc_info()))
                    continue
                if not plac_core.iterable(result):
                    task = Task(no, arglist, gen_value(result))
                elif cmd in self.tm.asyncommands:
                    task = AsynTask(no, arglist, result)
                    task.eventloop = self.eventloop
                elif cmd in self.tm.mpcommands:
                    task = MPTask(no, arglist, result)
                else: # blocking task
                    task = Task(no, arglist, result)
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

    def doctest(self, lineiter, put=write, verbose=False):
        """
        Parse a text containing doctests in a context and tests of all them.
        Raise an error even if a single doctest if broken. Use this for
        sequential tests which are logically grouped.
        """
        with self:
            for input, output, no in self._parse_doctest(lineiter):
                if verbose:
                    put('i> %s\n' % input)
                    put('-> %s\n' % output)
            out = self.send(input)
            if not out.str == output:
                msg = 'line %d: input: %s\noutput: %s\nexpected: %s\n' % (
                    no + 1, input, out, output)
                put(msg)
                raise out.etype, out.exc, out.tb

    def execute(self, lineiter, put=write, verbose=False):
        """
        Execute a lineiter of commands in a context and print the output.
        """
        with self:
            for line in lineiter:
                if verbose:
                    put('i> ' + line)
                output = self.send(line)
                if output.etype: # there was an error
                    raise output.etype, output.exc, output.tb
                put('%s\n' % output.str)

    def interact(self, stdin=sys.stdin, put=write, verbose=False):
        """
        Starts an interactive command loop reading commands from the
        consolle. Using rlwrap is recommended.
        """
        self.stdin = stdin
        self.put = put
        try:
            put(self.obj.intro + '\n')
        except AttributeError: # no intro
            put(self.p.format_usage() + '\n')
        put(self.prompt)
        with self:
            if self.tm.asyncommands:
                loop.queue_task(0, self._dispatch_async_input)
                loop.run()
            else:
                while True:
                    line = stdin.readline() # including \n
                    if not line:
                        break
                    task = self.maketask(line)
                    self.tm.run_task(task)
                    if verbose and task.synchronous and task.etype:
                        put(task.traceback + '\n')
                    put(str(task) + '\n')
                    put(self.prompt)

    def _dispatch_async_input(self):
        i, o, e = select.select([self.stdin], [], [], 0)
        if i:
            line = i[0].readline() # including \n
            if not line: # stdin was closed
                self.loop.halt()
                return
            task = self.maketask(line)
            self.tm.run_task(task)
            self.put('%s\n' % task)
            self.put(self.prompt)
        self.loop.queue_task(0, self._dispatch_async_input) # reschedule

################################## others ####################################

def cmd_interface(obj):
    "Returns a cmd.Cmd wrapper over the command container"
    i = Interpreter(obj)
    def default(self, line):
        print(i.send(line))
    dic = dict(preloop=lambda self: i.__enter__(),
               postloop=lambda self: i.__exit__(),
               do_EOF=lambda self, line: True,
               default=default,
               intro=getattr(i, 'intro', None))
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

class FakeOut(object):
    def __init__(self):
        self._s = ''
    def write(self, s):
        self._s += s
    def __str__(self):
        return self._s

def cmd_help(cmds, displaywidth=80, cmd=cmd.Cmd(stdout=FakeOut())): 
    cmd.stdout.write("%s\n" % str(cmd.doc_leader))
    cmd.print_topics(cmd.doc_header,   cmds,   15,80)
    #cmd.print_topics(cmd.misc_header,  helps,15,80)
    #cmd.print_topics(cmd.undoc_header, cmds_undoc, 15,80)
    return cmd.stdout
