"""
You can run this script as
$ python read_stdin.py < ishelve.bat
"""
from __future__ import with_statement
import sys
from ishelve import ishelve
import plac

if __name__ == '__main__':
    with plac.Interpreter(ishelve) as i:
        for line in sys.stdin:
            print(i.send(line))
