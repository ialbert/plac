# example13.py
import plac

@plac.flg('global_')
@plac.flg('dry_run')
@plac.opt('sys_')
def main(dry_run=False, global_=False, sys_=100):
    print (dry_run)
    print (global_)
    print (sys_)

if __name__ == '__main__':
    plac.call(main)
