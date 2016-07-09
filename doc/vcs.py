"A Fake Version Control System"

import plac  # this implementation also works with Python 2.4

commands = 'checkout', 'commit', 'status'


@plac.annotations(url='url of the source code')
def checkout(url):
    "A fake checkout command"
    return ('checkout ', url)


@plac.annotations(message=('commit message', 'option'))
def commit(message):
    "A fake commit command"
    return ('commit ', message)


@plac.annotations(quiet=('summary information', 'flag', 'q'))
def status(quiet):
    "A fake status command"
    return ('status ', quiet)


def __missing__(name):
    return ('Command %r does not exist' % name,)


def __exit__(etype, exc, tb):
    "Will be called automatically at the end of the intepreter loop"
    if etype in (None, GeneratorExit):  # success
        print('ok')

main = __import__(__name__)  # the module imports itself!

if __name__ == '__main__':
    import plac
    for out in plac.call(main, version='0.1.0'):
        print(out)
