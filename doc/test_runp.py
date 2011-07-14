"""
This test should work on Linux if you have Tkinter installed.
"""

from __future__ import with_statement
import plac, time

def gen(n):
    for i in range(n + 1):
        yield str(i)
        time.sleep(.1)

def err():
    yield 1/0

def test1():
    assert ['3', '5', '10'] == plac.runp([gen(3), gen(5), gen(10)])

def test2():
    result, error = plac.runp([gen(3), err()])
    assert result == '3' and error.__class__ == ZeroDivisionError

def test3():
    t0 = time.time()
    plac.runp([gen(9), gen(9)])
    assert int(time.time() - t0) == 1 # it must take 1 second, not 2


