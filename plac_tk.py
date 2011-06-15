import os, sys, plac_core
from Tkinter import Tk
from ScrolledText import ScrolledText
from plac_ext import Monitor, TerminatedProcess

class TkMonitor(Monitor):
    """
    An interface over a dictionary {taskno: scrolledtext widget}, with
    methods add_listener, del_listener, notify_listener and run.
    """
    def __init__(self, name):
        self.name = name
        self.widgets = {}

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def add_listener(self, taskno):
        "There is a ScrolledText for each task"
        st = ScrolledText(self.root, height=5)
        st.insert('end', 'Output of task %d\n' % taskno)
        st.pack()
        self.widgets[taskno] = st

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def del_listener(self, taskno):
        del self.widgets[taskno]

    @plac_core.annotations(taskno=('task number', 'positional', None, int))
    def notify_listener(self, taskno, msg):
        w = self.widgets[taskno]
        w.insert('end', msg + '\n')
        w.update()

    def run(self):
        'Start the mainloop'
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print >> sys.stderr, 'Process %d killed by CTRL-C' % os.getpid()
        except TerminatedProcess:
            pass
        finally:
            self.root.quit()

    def __enter__(self):
        self.root = Tk()
        self.root.title(self.name)
        self.root.wm_protocol("WM_DELETE_WINDOW", self.root.quit)
        return self

    def __exit__(self, exctype, exc, tb):
        self.stop()

    def schedule(self, seconds, func, arg):
        "Call func with arg after seconds"
        self.root.after(int(seconds*1000), func, arg)
