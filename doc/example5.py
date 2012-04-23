# example5.py
from datetime import date

def main(dsn, table='product', today=date.today()):
    "Do something on the database"
    print(dsn, table, today)

if __name__ == '__main__':
    import plac; plac.call(main)
