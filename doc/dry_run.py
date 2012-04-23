def main(dry_run: ('Dry run', 'flag', 'd')):
    if dry_run:
        print('Doing nothing')
    else:
        print('Doing something')

if __name__ == '__main__':
    import plac; plac.call(main)
