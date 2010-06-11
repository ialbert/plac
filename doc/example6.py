# example6.py
def main(dsn, command: ("SQL query", 'option')):
    print('executing %r on %s' % (command, dsn))

if __name__ == '__main__':
    import plac; plac.call(main)
