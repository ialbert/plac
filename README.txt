plac, the smartest command line arguments parser in the world
=============================================================

:Author: Michele Simionato
:E-mail: michele.simionato@gmail.com
:Requires: Python 2.3+
:Download page: http://pypi.python.org/pypi/plac
:Installation: ``easy_install -U plac``
:License: BSD license

Installation
-------------

If you are lazy, just perform

::

 $ easy_install -U plac

which will install the module on your system (and possibly argparse
too, if it is not already installed). Notice that Python 3 requires
the easy_install version of the distribute_ project.

If you prefer to install the full distribution from source, including
the documentation, download the tarball_, unpack it and run

::

 $ python setup.py install

in the main directory, possibly as superuser.

.. _tarball: http://pypi.python.org/pypi/plac
.. _distribute: http://packages.python.org/distribute/

Testing
--------

Run

::

 $ python doc/test_plac.py

or

::

 $ nosetests doc

or

::

 $ py.test doc

Documentation
--------------

You can choose between the `HTML version`_  and the `PDF version`_:

.. _HTML version: http://micheles.googlecode.com/hg/plac/doc/plac.html
.. _PDF version: http://micheles.googlecode.com/hg/plac/doc/plac.pdf

There is also an additional documentation for advanced usages of plac,
such as using plac_ for testing/scripting an application and to
write domain specific languages (DSL):

.. _HTML version: http://micheles.googlecode.com/hg/plac/doc/plac_adv.html
.. _PDF version: http://micheles.googlecode.com/hg/plac/doc/plac_adv.pdf
