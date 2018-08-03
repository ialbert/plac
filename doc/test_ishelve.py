# test_ishelve.py
import plac
import ishelve


def test():
    assert plac.call(ishelve.main, ['.clear']) == ['cleared the shelve']
    assert plac.call(ishelve.main, ['a=1']) == ['setting a=1']
    assert plac.call(ishelve.main, ['a']) == ['1']
    assert plac.call(ishelve.main, ['.delete=a']) == ['deleted a']
    assert plac.call(ishelve.main, ['a']) == ['a: not found']


if __name__ == '__main__':
    test()
