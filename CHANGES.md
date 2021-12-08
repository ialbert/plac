HISTORY
-------

## [Unreleased]

## 1.3.4 (2021-12-06)

Ensured tests using plac_runner use the same version of Python as them.
Fixed the tests on Python 3.9 and 3.10 and enabled Travis for them.
Prevent the tests from cluttering the test user's home directory.
Removed the pre-generated documentation, please use Read the Docs.
Cleaned up many minor issues in the documentation.
Removed use of obsolete SQLSoup library and features that used it.
Fixed issue with str as type hint.
Added more tests/examples.

## 1.3.0 (2021-01-02)

Thanks to Istvan Albert, it is now possible to use language keywords and
builtins as option/flag names. Some broken links were fixed and the
documentation has been moved to https://plac.readthedocs.io,
while the CI framework has changed from Travis to GitHub actions.

##  1.2.0 (2020-06-05)

Added dedenting of usage docstrings, as requested by Istvan Albert.
Added new decorators `plac.pos`, `plac.opt`, `plac.flg` and an example
using them in a section "For the impatient".
Added tests on travis for Python 3.8.

##  1.1.3 (2018-10-27)

Fixed some issues with kwargs parsing, docstring formatting and empty
string defaults reported by the user https://github.com/isaacto. Changed
the testing framework on travis from nosetest to pytest. Ported the
documentation to sphinx.

## 1.1.0 (2018-07-28)

Extended the recognition of default types to date and datetime in ISO
format. Fixed a bug when running plac scripts from Jupyter notebooks,
signaled by https://github.com/ursachi and https://github.com/rkpatel33.
Moreover, at user request, removed a Python 3.7 deprecation warning,
added a LICENSE.txt file and a Quickstart section to the README. plac
is tested on Travis for Python 2.7 and 3.4+ but it should work also
for all the other 3.X releases.

## 1.0.0 (2018-08-03)

New feature, requested by John Didion: if the type of an argument is not
specified but there is a default value, it is inferred from it. This is
experimental and works only for Python literal types.
Fixed a bug caused by arguments with default None in newer versions of argparse.
Added a `gh-pages` branch with the documentation, as suggested by Ryan Gonzalez.
Extended the Travis testing to Python 3.6. Python 2.6 still works but it is
untested and therefore deprecated.

## 0.9.6  (2016-07-09)

Solved an issue with non-ASCII characters; now any UTF-8 character
can go in the help message. Added support for `--version` in plac.call.
Modernized the changelog https://keepachangelog.com/

## 0.9.5 (2016-06-09)

Removed a usage of `print >>` that was breaking Python 3, signaled
by Quentin Pradet

## 0.9.4 (2016-06-09)

Removed use_2to3 in setup.py which was breaking Python 2, signaled
by Quentin Pradet

## 0.9.3 (2016-06-07)

Fixed the tests on Python 3 and produced a universal wheel instead of
relying on 2to3. Enabled Travis builds for Python 3.3, 3.4, 3.5

## 0.9.2 (2016-06-07)

Moved the repository from GoogleCode to GitHub. Included the doc fixes
by Nicola Larosa and polished the code base to be PEP 8 compliant.
Enabled Travis builds for Python 2.6 and 2.7

## 0.9.1 (2012-04-23)

Options and flags can now contain dashes (i.e. ``--dry-run`` is valid and
translated into dry_run, you are not forced to use ``--dry-run`` anymore);
restored the monitor support temporarily removed in 0.9.0, fixed an issue
with tuple defaults and fixed the display of the help command; specified
which features are experimental and which features are fully supported

## 0.9.0 (2011-06-19)

Default values are now displayed in the help message by default;
removed .help and introduced help; removed the special dotted
commands from the usage message; added an ``Interpreter.Exit``
exception; removed the experimental monitor framework because
it is too much platform-dependent; added a reference
to Argh; now plac has its own space on Google Code

## 0.8.1 (2011-04-11)

Removed a stray newline in the output of plac, as signaled
by Daniele Pighin; fixed a bug in the doctest method raising
non-existing exceptions; turned the notification messages into
unicode strings; removed an ugly SystemExit message
for invalid commands, signaled by Tuk Bredsdorff

## 0.8.0 (2011-02-16)

Added a monitor framework and a TkMonitor

## 0.7.6 (2011-01-13)

Fixed the error propagation in ``Interpreter.__exit__``.
Added a note about commandline and marrow.script in the documentation

## 0.7.5 (2011-01-01)

Fixed a bug with the help of subcommands, signaled by Paul Jacobson;
added the ability to save the output of a command into a file; postponed
the import of the readline module to avoid buffering issues; fixed a
bug with the traceback when in multiprocessing mode

## 0.7.4 (2010-09-04)

Fixed the plac_runner switches -i and -s; fixed a bug with multiline
output and issue with nosetest

## 0.7.3 (2010-08-31)

Put the documentation in a single document; added runp

## 0.7.2 (2010-08-11)

Interpreter.call does not start an interpreter automagically anymore;
better documented and added tests for the metavar concept (2010-08-31)

## 0.7.1 (2010-08-11)

A few bug fixes

## 0.7.0 (2010-08-07)

Improved and documented the support for parallel programming;
added an asynchronous server; added plac.Interpreter.call

## 0.6.1 (2010-07-12)

Fixed the history file location; added the ability to pass a split
function; added two forgotten files; added a reference to cmd2 by
Catherine Devlin

## 0.6.0 (2010-07-11)

Improved the interactive experience with full readline support and
custom help. Added support for long running command, via threads and
processes

## 0.5.0 (2010-06-20)

Gigantic release. Introduced smart options, added an Interpreter class
and the command container concept. Made the split plac/plac_core/plac_ext
and added a plac runner, able to run scripts, batch files and doctests.
Removed the default formatter class

## 0.4.3 (2010-06-11)

Fixed the installation procedure to automatically download argparse
if needed

## 0.4.2 (2010-06-04)

Added missing .help files, made the tests generative and added a
note about Clap in the documentation

## 0.4.1 (2010-06-03)

Changed the default formatter class and fixed a bug in the
display of the default arguments. Added more stringent tests.

## 0.4.0 (2010-06-03)

abbrev is now optional. Added a note about CLIArgs and opterate.
Added keyword arguments recognition. ``plac.call`` now returns the
the output of the main function.

## 0.3.0 (2010-06-02)

First released version.
