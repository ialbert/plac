"A Fake Version Control System"

import plac

commands = 'checkout', 'commit', 'status'

@plac.annotations(
    url=('url of the source code', 'positional'))
def checkout(url):
    return ('checkout ', url)

@plac.annotations(
    message=('commit message', 'option'))
def commit(message):
    return ('commit ', message)

@plac.annotations(quiet=('summary information', 'flag'))
def status(quiet):
    return ('status ', quiet)

if __name__ == '__main__':
    import __main__
    print(plac.call(__main__))
