# example13.py
import plac


@plac.flg('list_')  # avoid clash with builtin
@plac.flg('yield_')  # avoid clash with keyword
@plac.opt('sys_')  # avoid clash with a very common name
def main(list_, yield_=False, sys_=100):
    print(list_)
    print(yield_)
    print(sys_)


if __name__ == '__main__':
    plac.call(main)
