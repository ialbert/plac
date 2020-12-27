# example12.py
import plac


@plac.annotations(
   opt=('some option', 'option'),
   args='default arguments',
   kw='keyword arguments')
def main(opt, *args, **kw):
    if opt:
       yield 'opt=%s' % opt
    if args:
       yield 'args=%s' % str(args)
    if kw:
       yield 'kw=%s' % kw

if __name__ == '__main__':
    for output in plac.call(main):
       print(output)
