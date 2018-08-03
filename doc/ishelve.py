# ishelve.py
import os
import shelve
import plac

DEFAULT_SHELVE = os.path.expanduser('~/conf.shelve')


@plac.annotations(
    help=('show help', 'flag'),
    showall=('show all parameters in the shelve', 'flag'),
    clear=('clear the shelve', 'flag'),
    delete=('delete an element', 'option'),
    filename=('filename of the shelve', 'option'),
    params='names of the parameters in the shelve',
    setters='setters param=value')
def main(help, showall, clear, delete, filename=DEFAULT_SHELVE,
         *params, **setters):
    "A simple interface to a shelve. Use .help to see the available commands."
    sh = shelve.open(filename)
    try:
        if not any([help, showall, clear, delete, params, setters]):
            yield ('no arguments passed, use .help to see the '
                   'available commands')
        elif help:  # custom help
            yield 'Commands: .help, .showall, .clear, .delete'
            yield '<param> ...'
            yield '<param=value> ...'
        elif showall:
            for param, name in sh.items():
                yield '%s=%s' % (param, name)
        elif clear:
            sh.clear()
            yield 'cleared the shelve'
        elif delete:
            try:
                del sh[delete]
            except KeyError:
                yield '%s: not found' % delete
            else:
                yield 'deleted %s' % delete
        for param in params:
            try:
                yield sh[param]
            except KeyError:
                yield '%s: not found' % param
        for param, value in setters.items():
            sh[param] = value
            yield 'setting %s=%s' % (param, value)
    finally:
        sh.close()


main.add_help = False  # there is a custom help, remove the default one
main.prefix_chars = '.'  # use dot-prefixed commands

if __name__ == '__main__':
    for output in plac.call(main):
        print(output)
