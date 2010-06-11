import plac
from example13 import FVCS

class VCS_with_help(FVCS):
    commands = FVCS.commands + ('help',)

    @plac.annotations(
        name=('a recognized command', 'positional', None, str, commands))
    def help(self, name):
        self.p.subp[name].print_help()

main = VCS_with_help()

if __name__ == '__main__':
    plac.call(main)
