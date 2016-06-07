# dbcli.py
import plac
from sqlsoup import SQLSoup


@plac.annotations(
    db=plac.Annotation("Connection string", type=SQLSoup),
    header=plac.Annotation("Header", 'flag', 'H'),
    sqlcmd=plac.Annotation("SQL command", 'option', 'c', str, metavar="SQL"),
    delimiter=plac.Annotation("Column separator", 'option', 'd'),
    scripts=plac.Annotation("SQL scripts"))
def main(db, header, sqlcmd, delimiter="|", *scripts):
    "A script to run queries and SQL scripts on a database"
    yield 'Working on %s' % db.bind.url

    if sqlcmd:
        result = db.bind.execute(sqlcmd)
        if header:  # print the header
            yield delimiter.join(result.keys())
        for row in result:  # print the rows
            yield delimiter.join(map(str, row))

    for script in scripts:
        db.bind.execute(open(script).read())
        yield 'executed %s' % script

if __name__ == '__main__':
    for output in plac.call(main):
        print(output)
