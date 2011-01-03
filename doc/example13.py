import plac

class FVCS(object):
    "A Fake Version Control System"
    commands = 'checkout', 'commit', 'status', 'help'
    add_help = True

    @plac.annotations(
        name=('a recognized command', 'positional', None, str, commands))
    def help(self, name):
        print(plac.parser_from(self).help_cmd(name))

    @plac.annotations(
        url=('url of the source code', 'positional'))
    def checkout(self, url):
        print('checkout', url)

    def commit(self):
        print('commit')

    @plac.annotations(quiet=('summary information', 'flag'))
    def status(self, quiet):
        print('status', quiet)

main = FVCS()

if __name__ == '__main__':
    plac.call(main)
