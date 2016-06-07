import os
import plac
from sqlsoup import SQLSoup

SQLKEYWORDS = set(['help', 'select', 'from', 'inner', 'join', 'outer',
                   'left', 'right'])  # and many others

DBTABLES = set(['table1', 'table2'])  # you can read them from the db schema

COMPLETIONS = SQLKEYWORDS | DBTABLES


class SqlInterface(object):
    commands = ['SELECT']

    def __init__(self, dsn):
        self.soup = SQLSoup(dsn)

    def SELECT(self, argstring):
        sql = 'SELECT ' + argstring
        for row in self.soup.bind.execute(sql):
            yield str(row)  # the formatting can be much improved


rl_input = plac.ReadlineInput(
    COMPLETIONS, histfile=os.path.expanduser('~/.sql_interface.history'),
    case_sensitive=False)


def split_on_first_space(line, commentchar):
    return line.strip().split(' ', 1)  # ignoring comments

if __name__ == '__main__':
    plac.Interpreter.call(SqlInterface, split=split_on_first_space,
                          stdin=rl_input, prompt='sql> ')
