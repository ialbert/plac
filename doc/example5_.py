# example5_.py
from datetime import date

# the first example with a function annotation
def main(dsn: "the database dsn", table='product', today=date.today()):
    "Do something on the database"
    print(dsn, table, today)

if __name__ == '__main__':
    import plac; plac.call(main)
