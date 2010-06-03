# example12.py
import plac

@plac.annotations(
   opt=('some option', 'option'),
   args='default arguments',
   kw='keyword arguments')
def main(opt, *args, **kw):
   print(opt, args, kw)

if __name__ == '__main__':
    plac.call(main)
