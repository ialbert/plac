"""
The tests should be run as standalone script
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

sys_argv0 = sys.argv[0]
docdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(docdir)
PLAC_RUNNER = os.path.join(os.path.dirname(docdir), 'plac_runner.py')


# ####################### helpers ###################### #

def fix_today(text):
    return text.replace('YYYY-MM-DD', str(datetime.date.today()))


def expect(errclass, func, *args, **kw):
    try:
        func(*args, **kw)
    except errclass:
        pass
    else:
        raise RuntimeError('%s expected, got none!' % errclass.__name__)


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


def check_help(name):
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
        expected = fix_today(open(name + '.help').read()).strip()
        got = p.format_help().strip()
        assert got == expected, got
    finally:
        sys.argv[0] = sys_argv0

# ###################### tests ########################### #


def test_expected_help():
    for fname in os.listdir('.'):
        if fname.endswith('.help'):
            name = fname[:-5]
            if name not in ('vcs', 'ishelve'):
                check_help(fname[:-5])


p1 = parser_from(lambda delete, *args: None,
                 delete=('delete a file', 'option'))


def test_p1():
    arg = p1.parse_args(['-d', 'foo', 'arg1', 'arg2'])
    assert arg.delete == 'foo'
    assert arg.args == ['arg1', 'arg2']

    arg = p1.parse_args([])
    assert arg.delete is None, arg.delete
    assert arg.args == [], arg.args


p2 = parser_from(lambda arg1, delete, *args: None,
                 delete=('delete a file', 'option', 'd'))


def test_p2():
    arg = p2.parse_args(['-d', 'foo', 'arg1', 'arg2'])
    assert arg.delete == 'foo', arg.delete
    assert arg.arg1 == 'arg1', arg.arg1
    assert arg.args == ['arg2'], arg.args

    arg = p2.parse_args(['arg1'])
    assert arg.delete is None, arg.delete
    assert arg.args == [], arg.args
    assert arg, arg

    expect(SystemExit, p2.parse_args, [])


p3 = parser_from(lambda arg1, delete: None,
                 delete=('delete a file', 'option', 'd'))


def test_p3():
    arg = p3.parse_args(['arg1'])
    assert arg.delete is None, arg.delete
    assert arg.arg1 == 'arg1', arg.args

    expect(SystemExit, p3.parse_args, ['arg1', 'arg2'])
    expect(SystemExit, p3.parse_args, [])


p4 = parser_from(lambda delete, delete_all, color="black": None,
                 delete=('delete a file', 'option', 'd'),
                 delete_all=('delete all files', 'flag', 'a'),
                 color=('color', 'option', 'c'))


def test_p4():
    arg = p4.parse_args(['-a'])
    assert arg.delete_all is True, arg.delete_all

    arg = p4.parse_args([])

    arg = p4.parse_args(['--color=black'])
    assert arg.color == 'black'

    arg = p4.parse_args(['--color=red'])
    assert arg.color == 'red'


p5 = parser_from(lambda dry_run=False: None, dry_run=('Dry run', 'flag', 'x'))


def test_p5():
    arg = p5.parse_args(['--dry-run'])
    assert arg.dry_run is True,  arg.dry_run

p_global = parser_from(lambda reserved_=False: None, reserved_=('Reserved word', 'flag', 'g'))

def test_global():
    arg = p_global.parse_args(['--reserved'])
    assert arg.reserved is True,  arg.reserved


def test_flag_with_default():
    expect(TypeError, parser_from, lambda yes_or_no='no': None,
           yes_or_no=('A yes/no flag', 'flag', 'f'))


def assert_usage(parser, expected):
    usage = parser.format_usage()
    assert usage == expected, usage


def test_metavar_no_defaults():
    sys.argv[0] = 'test_plac.py'

    # positional
    p = parser_from(lambda x: None,
                    x=('first argument', 'positional', None, str,
                       [], 'METAVAR'))
    assert_usage(p, 'usage: test_plac.py [-h] METAVAR\n')

    # option
    p = parser_from(lambda x: None,
                    x=('first argument', 'option', None, str, [], 'METAVAR'))
    assert_usage(p, 'usage: test_plac.py [-h] [-x METAVAR]\n')
    sys.argv[0] = sys_argv0


def test_metavar_with_defaults():
    sys.argv[0] = 'test_plac.py'

    # positional
    p = parser_from(lambda x='a': None,
                    x=('first argument', 'positional', None, str,
                       [], 'METAVAR'))
    assert_usage(p, 'usage: test_plac.py [-h] [METAVAR]\n')

    # option
    p = parser_from(lambda x='a': None,
                    x=('first argument', 'option', None, str,
                       [], 'METAVAR'))
    assert_usage(p, 'usage: test_plac.py [-h] [-x METAVAR]\n')

    p = parser_from(lambda x='a': None,
                    x=('first argument', 'option', None, str, []))
    assert_usage(p, 'usage: test_plac.py [-h] [-x a]\n')

    sys.argv[0] = sys_argv0


def test_metavar_empty_string():
    # see https://github.com/ialbert/plac/issues/36
    def main(arg=''):
        pass
    sys.argv[0] = 'test_plac.py'
    p = parser_from(main)
    assert_usage(p, "usage: test_plac.py [-h] ['']\n")
    sys.argv[0] = sys_argv0


def test_kwargs():
    def main(opt, arg1, *args, **kw):
        print(opt, arg1)
        return args, kw
    main.__annotations__ = dict(opt=('Option', 'option'))
    argskw = plac.call(main, ['arg1', 'arg2', 'a=1', 'b=2'])
    assert argskw == [('arg2',), {'a': '1', 'b': '2'}], argskw

    argskw = plac.call(main, ['arg1', 'arg2', 'a=1', '-o', '2'])
    assert argskw == [('arg2',), {'a': '1'}], argskw

    expect(SystemExit, plac.call, main, ['arg1', 'arg2', 'a=1', 'opt=2'])


def test_kwargs2():
    # see https://github.com/ialbert/plac/issues/39
    def main(**kw):
        return kw.items()
    assert plac.call(main, ['a=1']) == [('a', '1')]
    expect(SystemExit, plac.call, main, ['foo'])
    expect(SystemExit, plac.call, main, ['foo', 'a=1'])


def test_kwargs3():
    # see https://github.com/ialbert/plac/issues/38
    def main(opt='foo', **kw):
        return opt, kw
    main.__annotations__ = dict(opt=('Option', 'option'))
    assert plac.call(main, ['-o', 'abc=']) == ['abc=', {}]
    assert plac.call(main, ['-o', 'abc=', 'z=1']) == ['abc=', {'z': '1'}]
    assert plac.call(main, ['z=1']) == ['foo', {'z': '1'}]


def test_date_default():
    p = parser_from(lambda day=datetime.date.today(): day)
    arg = p.parse_args(['2019-11-19'])
    assert arg.day == datetime.date(2019, 11, 19)


def test_int_default():
    p = parser_from(lambda number=42: number)
    arg = p.parse_args([])
    assert arg.number == 42
    arg = p.parse_args(['424242'])
    assert arg.number == 424242


def test_none_default():
    p = parser_from(lambda nonable=None: arg)
    arg = p.parse_args([])
    assert arg.nonable is None
    arg = p.parse_args(['somestring'])
    assert arg.nonable == 'somestring'


class Cmds(object):
    add_help = False
    commands = 'help', 'commit'

    def help(self, name):
        return 'help', name

    def commit(self):
        return 'commit'


cmds = Cmds()


def test_cmds():
    assert 'commit' == plac.call(cmds, ['commit'])
    assert ['help', 'foo'] == plac.call(cmds, ['help', 'foo'])
    expect(SystemExit, plac.call, cmds, [])


def test_cmd_abbrevs():
    assert 'commit' == plac.call(cmds, ['comm'])
    assert ['help', 'foo'] == plac.call(cmds, ['h', 'foo'])
    expect(SystemExit, plac.call, cmds, ['foo'])


def test_sub_help():
    c = Cmds()
    c.add_help = True
    expect(SystemExit, plac.call, c, ['commit', '-h'])


def test_yield():
    def main():
        for i in (1, 2, 3):
            yield i
    assert plac.call(main, []) == [1, 2, 3]


def test_doctest():
    failure, tot = doctest.testfile('index.rst', module_relative=False)
    assert not failure, failure


failing_scripts = set(['ishelve2.plac'])


def check_script(args):
    if failing_scripts.intersection(args):
        assert subprocess.call(args) > 0, (  # expected failure
            'Unexpected success for %s' % ' '.join(args))
    else:
        assert subprocess.call(args) == 0, 'Failed %s' % ' '.join(args)


'''
# Disabling unused functionality
def test_batch():
    for batch in os.listdir('.'):
        if batch.endswith('.plac'):
            check_script([sys.executable, PLAC_RUNNER, '-b', batch])


def test_placet():
    for placet in os.listdir('.'):
        if placet.endswith('.placet'):
            check_script([sys.executable, PLAC_RUNNER, '-t', placet])
'''

if __name__ == '__main__':
    n = 0
    for name, test in sorted(globals().items()):
        if name.startswith('test_'):
            print('Running ' + name)
            maybegen = test()
            if hasattr(maybegen, '__iter__'):
                for func, arg in maybegen:
                    func(arg)
                    n += 1
            else:
                n += 1
    print('Executed %d tests OK' % n)
