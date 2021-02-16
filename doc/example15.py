# example15.py
# Tests choices on variable number of option arguments
import plac

@plac.pos('args', help="words")
@plac.opt('kwds', help="key=value", )
def main(*args, **kwds):
    print(args)
    print(kwds)

if __name__ == '__main__':
    plac.call(main)