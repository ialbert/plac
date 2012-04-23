# ishelve3.py
from ishelve2 import ShelveInterface

if __name__ == '__main__':
    import plac; plac.Interpreter.call(ShelveInterface)

## try the following:
# $ python ishelve3.py delete
# $ python ishelve3.py set a 1
# $ python ishelve3.py showall
