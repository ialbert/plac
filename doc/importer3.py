import time
import plac

class FakeImporter(object):
    "A fake importer with an import_file command"
    mpcommands = ['import_file']
    def __init__(self, dsn):
        self.dsn = dsn
    def import_file(self, fname):
        "Import a file into the database"
        try:
            for n in range(10000):
                time.sleep(.02)
                if n % 100 == 99:
                    yield 'Imported %d lines' % (n+1)
        finally:
            print('closing the file')

if __name__ == '__main__':
    plac.Interpreter.call(FakeImporter)
