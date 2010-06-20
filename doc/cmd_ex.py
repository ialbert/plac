# cmd_ext.py
from plac_ext import cmd_interface
import ishelve2

if __name__ == '__main__':
    cmd_interface(ishelve2.main()).cmdloop()
