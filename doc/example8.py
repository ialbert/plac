# example8.py
def main(command: ("SQL query", 'option', 'q'), dsn):
    if command:
        print('executing %s on %s' % (command, dsn))
        # ...

if __name__ == '__main__':
    import plac; plac.call(main)
