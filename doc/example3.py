# example3.py
def main(dsn):
    "Do something with the database"
    print(dsn)
    # ...
 
if __name__ == '__main__':
    import plac; plac.call(main)
