"""
The tests are runnable with nose, with py.test, or even as standalone script
"""

import os, sys
import plac

sys.path.insert(0, 'doc')

######################## helpers #######################

def expect(errclass, func, *args, **kw):
    try:
        func(*args, **kw)
    except errclass:
        pass
    else:
        raise RuntimeError('%s expected, got none!', errclass.__name__)

def parser_from(f, **kw):
    f.__annotations__ = kw
    return plac.parser_from(f)

def check_help(name):
    sys.argv[0] = name + '.py'
    dic = {}
    try:
        execfile(os.path.join('doc', name + '.py'), dic)
    except NameError: # Python 3
        exec(open(os.path.join('doc', name + '.py')).read(), dic)
    except SyntaxError: # raised by some tests when using Python 2
        return
    p = plac.parser_from(dic['main'])
    expected = open(os.path.join('doc', name + '.help')).read().strip()
    got = p.format_help().strip()
    assert got == expected, got

####################### tests ############################

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

def test_flag_with_default():
    expect(TypeError, parser_from, lambda yes_or_no='no': None,
           yes_or_no=('A yes/no flag', 'flag', 'f'))

def test_kwargs():
    def main(opt, arg1, *args, **kw):
        print(opt, arg1)
        return args, kw
    main.__annotations__ = dict(opt=('Option', 'option'))
    argskw = plac.call(main, ['arg1', 'arg2', 'a=1', 'b=2'])
    assert argskw == (('arg2',), dict(a='1', b='2')), argskw
    
    argskw = plac.call(main, ['arg1', 'arg2', 'a=1', '-o2'])
    assert argskw == (('arg2',), dict(a='1')), argskw

    expect(SystemExit, plac.call, main, ['arg1', 'arg2', 'a=1', 'opt=2'])

def test_expected_help():
    for fname in os.listdir('doc'):
        if fname.endswith('.help'):
            yield check_help, fname[:-5]

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
                n +=1
    print('Executed %d tests OK' % n)
