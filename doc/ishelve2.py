# ishelve2.py
import os
import shelve
import plac


class ShelveInterface(object):
    "A minimal interface over a shelve object."
    commands = 'set', 'show', 'showall', 'delete'

    @plac.annotations(
        configfile=('path name of the shelve', 'option'))
    def __init__(self, configfile):
        self.configfile = configfile or 'conf.shelve'
        self.fname = os.path.expanduser(self.configfile)
        self.__doc__ += ('\nOperating on %s.\nUse help to see '
                         'the available commands.\n' % self.fname)

    def __enter__(self):
        self.sh = shelve.open(self.fname)
        return self

    def __exit__(self, etype, exc, tb):
        self.sh.close()

    def set(self, name, value):
        "set name value"
        yield 'setting %s=%s' % (name, value)
        self.sh[name] = value

    def show(self, *names):
        "show given parameters"
        for name in names:
            yield '%s = %s' % (name, self.sh[name])  # no error checking

    def showall(self):
        "show all parameters"
        for name in self.sh:
            yield '%s = %s' % (name, self.sh[name])

    def delete(self, name=''):
        "delete given parameter (or everything)"
        if name == '':
            yield 'deleting everything'
            self.sh.clear()
        else:
            yield 'deleting %s' % name
            del self.sh[name]  # no error checking


if __name__ == '__main__':
    plac.Interpreter(plac.call(ShelveInterface)).interact()
