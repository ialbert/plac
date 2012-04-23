from __future__ import with_statement
from Tkinter import *
from importer3 import FakeImporter

def taskwidget(root, task, tick=500):
    "A Label widget showing the output of a task every 500 ms"
    sv = StringVar(root)
    lb = Label(root, textvariable=sv)
    def show_outlist():
        try:
            out = task.outlist[-1]
        except IndexError: # no output yet
            out = ''
        sv.set('%s %s' % (task, out))
        root.after(tick, show_outlist)
    root.after(0, show_outlist)
    return lb

def monitor(tasks):
    root = Tk()
    for task in tasks:
        task.run()
        taskwidget(root, task).pack()
    root.mainloop()

if __name__ == '__main__':
    import plac
    with plac.Interpreter(plac.call(FakeImporter)) as i:
        tasks = [i.submit('import_file f1'), i.submit('import_file f2')]
        monitor(tasks)
