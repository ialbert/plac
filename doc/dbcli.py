# dbcli.py
import plac
from sqlalchemy.ext.sqlsoup import SqlSoup

@plac.annotations(
    db=("Connection string", 'positional', None, SqlSoup),
    header=("Header", 'flag', 'H'),
    sqlcmd=("SQL command", 'option', 'c', str, None, "SQL"),
    delimiter=("Column separator", 'option', 'd'),
    scripts="SQL scripts",
    )
def main(db, header, sqlcmd, delimiter="|", *scripts):
    "A script to run queries and SQL scripts on a database"
    print('Working on %s' % db.bind.url)
    if sqlcmd:
        result = db.bind.execute(sqlcmd)
        if header: # print the header
            print(delimiter.join(result.keys()))
        for row in result: # print the rows
            print(delimiter.join(map(str, row)))

    for script in scripts:
        db.bind.execute(file(script).read())

if __name__ == '__main__':
    plac.call(main)
