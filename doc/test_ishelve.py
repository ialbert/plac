# test_ishelve.py
import plac
from ishelve import ishelve

def test():
    assert plac.call(ishelve, []) == []
    assert plac.call(ishelve, ['.clear']) == ['cleared the shelve']
    assert plac.call(ishelve, ['a=1']) == ['setting a=1']
    assert plac.call(ishelve, ['a']) == ['1']
    assert plac.call(ishelve, ['.delete=a']) == ['deleted a']
    assert plac.call(ishelve, ['a']) == ['a: not found']

if __name__ == '__main__':
    test()
