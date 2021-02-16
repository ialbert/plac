# example14.py
# Tests choices on variable number of arguments
import plac

@plac.pos('words', help="Input words")
def main(*words):
    print(words)

if __name__ == '__main__':
    plac.call(main)