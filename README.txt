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

Some tests will fail if sqlalchemy is not installed. 
Run an ``easy_install -U sqlalchemy`` or just ignore them.

Documentation
--------------

The source code and the documentation are hosted on Google code.
Here is the full documentation in HTML and PDF form:

http://plac.googlecode.com/hg/doc/plac.html

http://plac.googlecode.com/hg/doc/plac.pdf
