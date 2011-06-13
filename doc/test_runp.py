"""
This test should work on Linux if you have Tkinter installed.
"""

from __future__ import with_statement
import plac, time

def gen(n):
    for i in range(n + 1):
        yield str(i)
        time.sleep(.1)

def test():
    tasks = plac.runp([gen(3), gen(5), gen(10)])
    for t in tasks:
        t.result
    t.man.stop()

#def test_tkmonitor():
#    mon = plac_tk.TkMonitor('tkmon')
#    results = plac.runp([gen(3), gen(5), gen(10)], monitors=[mon])
#    assert results == ['3', '5', '10']

