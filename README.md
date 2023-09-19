# Plac: parsing the command line the easy way

`plac` is a Python package that can generate command line parameters
from function signatures.

`plac` works on Python 2.6 through all versions of Python 3.

`plac` has no dependencies beyond modules already present in the Python
standard library.

`plac` implements most of its functionality in a single file that may be
included in your source code.

## Quickstart

`plac` automatically generates the command line parameters from the function signature. 
        
It offers three decorators to describe positional, option and flag type parameters:

```python
import plac

# Add decorators to the function
@plac.pos('model', help="model name", choices=['A', 'B', 'C'])
@plac.opt('iter', help="iterations", type=int)
@plac.flg('debug', help="debug mode")
def main(model, iter=100, debug=False):
    """
    A script for machine learning
    """
    print (model, iter, debug)

if __name__ == '__main__':
    # Execute function via plac.call()
    plac.call(main)
```

And that's it! The program can now take parameters from the command line like so:

    python example.py -d -i 1000 B 

Running the script with `python example.py -h` will give you the following help message: :

```
usage: example.py [-h] [-i 100] [-d] {A,B,C}

A script for machine learning

positional arguments:
  {A,B,C}             model name

options:
  -h, --help          show this help message and exit
  -i 100, --iter 100  iterations
  -d, --debug         debug mode
```

Running the script with no parameters `$ python example.py` would print:

```
usage: example.py [-h] [-i 100] [-d] {A,B,C}
example.py: error: the following arguments are required: model
```

## Decorator reference

To use `plac` all you need to know are the following three decorators:

* `@plac.pos` - for positional parameters `model`
* `@plac.opt` - for key value options `--iter 100`
* `@plac.flg` - for flags `--debug`

* that have the following signatures:

```python
# Positional parameters.
pos(arg, help=None, type=None, choices=None, metavar=None):

# Option parameters.
opt(arg, help=None, type=None, abbrev=None, choices=None, metavar=None):

# Flag parameters.
flg(arg, help=None, abbrev=None):
```

## Zero dependencies ... not even plac :-)

Notably, the main functionality of `plac` is implemented in a single
Python module called `plac_core.py` that, if necessary, may be included and
distributed with your source code thus reducing external dependencies in
your code.

Copy `plac_core.py` to your package then use it like so:

```python
from mypackage import plac_core as plac
```

## Avoiding name clashes

Python syntax, or your variable naming may impose constraints on what
words may be used as parameters. To circumvent that limitation append a
trailing underscore to the name. `plac` will strip that underscore from
the command line parameter name:

```python
import plac

@plac.flg('list_')   # avoid clash with builtin
@plac.flg('yield_')  # avoid clash with keyword
@plac.opt('sys_')    # avoid clash with a very common name
def main(list_, yield_=False, sys_=100):
    print(list_)
    print(yield_)
    print(sys_)

if __name__ == '__main__':
    plac.call(main)
```

produces the usage:

```
usage: example13.py [-h] [-l] [-y] [-s 100]

optional arguments:
  -h, --help         show this help message and exit
  -l, --list
  -y, --yield        [False]
  -s 100, --sys 100  [100]
```

## Variable arguments

`plac` may accept multiple positional arguments and even additional key=value pairs:

```python
import plac

@plac.pos('args', help="words")
@plac.opt('kwds', help="key=value", )
def main(*args, **kwds):
    print(args)
    print(kwds)

if __name__ == '__main__':
    plac.call(main)
```

the usage will be:

```
usage: example15.py [-h] [args ...] [kwds ...]

positional arguments:
  args        words
  kwds        key=value

optional arguments:
  -h, --help  show this help message and exit
```

when running it as:

    python example15.py A B x=10 y=20

the program prints:

    ('A', 'B')
    {'x': '10', 'y': '20'}

## Installation

    pip install plac

## Testing

Run

    python doc/test_plac.py

You will see several apparent errors, but this is right, since the tests
are checking for several error conditions. The important thing is that
you get a line like

`Executed XX tests OK`

## Code

-   <https://github.com/ialbert/plac>

Author: Michele Simionato, <michele.simionato@gmail.com>

Maintainer: Istvan Albert, <istvan.albert@gmail.com>

## Issues

-   <https://github.com/ialbert/plac/issues>

## License

BSD License
