import os, plac
from sqlalchemy.ext.sqlsoup import SqlSoup

SQLKEYWORDS = set(['select', 'from', 'inner', 'join', 'outer', 'left', 'right']
                  ) # and many others
DBTABLES = set(['table1', 'table2']) # you can read them from the db schema

COMPLETIONS = SQLKEYWORDS | DBTABLES

class SqlInterface(object):
    commands = ['SELECT']
    def __init__(self, dsn):
        self.soup = SqlSoup(dsn)
    def SELECT(self, *args):
        sql = 'SELECT ' + ' '.join(args)
        for row in self.soup.bind.execute(sql):
            yield str(row) # the formatting can be much improved

rl_input = plac.ReadlineInput(
    COMPLETIONS, prompt='sql> ', 
    histfile=os.path.expanduser('~/.sql_interface.history'), 
    case_sensitive=False)

if __name__ == '__main__':
    plac.Interpreter(plac.call(SqlInterface)).interact(rl_input)
