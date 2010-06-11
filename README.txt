plac, the easiest command line arguments parser in the world
============================================================

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

which will install just the module on your system. Notice that
Python 3 requires the easy_install version of the distribute_ project.

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

 $ python test_plac.py

or

::

 $ nosetests test_plac.py

or

::

 $ py.test test_plac.py

Documentation
--------------

You can choose between the `HTML version`_  and the `PDF version`_ .

.. _HTML version: http://micheles.googlecode.com/hg/plac/doc/plac.html
.. _PDF version: http://micheles.googlecode.com/hg/plac/doc/plac.pdf
