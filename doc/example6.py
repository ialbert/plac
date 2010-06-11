# example6.py
from datetime import datetime

def main(dsn, *scripts):
    "Run the given scripts on the database"
    for script in scripts:
        print('executing %s' % script)
        # ...

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        sys.exit('usage: python %s dsn script.sql ...' % sys.argv[0])
    main(sys.argv[1:])
