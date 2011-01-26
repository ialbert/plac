"""
This test should work on Linux if you have both Tkinter installed.
"""

from __future__ import with_statement
import plac, plac_tk, time

def gen(n):
    for i in range(n):
        yield str(i)
        time.sleep(.1)

def test():
    tasks = plac.runp([gen(3), gen(5), gen(10)])
    for t in tasks:
        t.result
    t.man.stop()

def test_tkmonitor():
    mon = plac_tk.TkMonitor('tkmon')
    tasks = plac.runp([gen(3), gen(5), gen(10)], monitors=[mon])
    for t in tasks:
        t.result
    t.man.stop()
