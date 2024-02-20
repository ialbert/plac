"""
Generates outputs for the tests based on a Python version
Used only when the output format of argparse changes
"""

import os
import sys
import argparse
import datetime
import doctest
import subprocess
import plac
import plac_core

version = sys.version_info[:2]

# The name of the directory that will store version specific outputs.
dirname = ".".join(map(str, version))
sys_argv0 = sys.argv[0]
docdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(docdir)


def parser_from(f, **kw):
    f.__annotations__ = kw
    return plac.parser_from(f)


# FIXME: Remove this when removing support for Python 3.8
class PlacTestFormatter(argparse.RawDescriptionHelpFormatter):
    if version < (3, 9):
        def _format_args(self, action, default_metavar):
            get_metavar = self._metavar_formatter(action, default_metavar)
            if action.nargs == argparse.ZERO_OR_MORE:
                metavar = get_metavar(1)
                if len(metavar) == 2:
                    result = '[%s [%s ...]]' % metavar
                else:
                    result = '[%s ...]' % metavar
            else:
                result = super(PlacTestFormatter, self)._format_args(
                    action, default_metavar)
            return result


def create_help(name):

    # The directory for the version.

    os.makedirs(dirname, exist_ok=True)
    sys.argv[0] = name + '.py'  # avoid issue with pytest
    plac_core._parser_registry.clear()  # makes different imports independent
    try:
        try:
            main = plac.import_main(name + '.py')
        except SyntaxError:
            if sys.version < '3':  # expected for Python 2.X
                return
            else:  # not expected for Python 3.X
                raise
        p = plac.parser_from(main, formatter_class=PlacTestFormatter)
        got = p.format_help().strip()
        help_name = dirname + '/' + name + '.help'
        fp = open(help_name, 'w')
        fp.write(got)
        fp.close()
    finally:
        sys.argv[0] = sys_argv0

# ###################### tests ########################### #


def generate_help():
    curr_dir = os.path.split(os.path.abspath(__file__))[0]
    print (curr_dir)

    for fname in os.listdir('.'):
        if fname.endswith('.help'):
            name = fname[:-5]
            if name not in ('vcs', 'ishelve'):
                create_help(fname[:-5])

if __name__ == '__main__':
    generate_help()
    #print('Executed %d tests OK' % n)
