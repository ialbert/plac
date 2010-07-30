import plac
from importer2 import FakeImporter
from ishelve2 import ShelveInterface

if __name__ == '__main__':
    main = FakeImporter('dsn')
    #main = ShelveInterface()
    plac.Interpreter(main).start_server() # default port 2199
