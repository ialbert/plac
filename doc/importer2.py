import time
import plac

class FakeImporter(object):
    "A fake importer with an import_file command"
    thcommands = ['import_file']
    def __init__(self, dsn):
        self.dsn = dsn
    def import_file(self, fname):
        "Import a file into the database"
        try:
            for n in range(10000):
                time.sleep(.02)
                if n % 100 == 99: # every two seconds
                    yield 'Imported %d lines' % (n+1)
                if n % 10 == 9: # every 0.2 seconds
                    yield # go back and check the TOBEKILLED status
        finally:
            print('closing the file')

if __name__ == '__main__':
    plac.Interpreter.call(FakeImporter)
