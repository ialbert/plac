import plac
from importer2 import FakeImporter

def main(port=2199):
    main = FakeImporter('dsn')
    plac.Interpreter(main).start_server(port)
    
if __name__ == '__main__':
   plac.call(main)
