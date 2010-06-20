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

The source code and the documentation are hosted on Google code.
First you should read the basic documentation:

http://micheles.googlecode.com/hg/plac/doc/plac.html

http://micheles.googlecode.com/hg/plac/doc/plac.pdf

There is also an additional documentation for advanced usages of plac,
such as using plac for testing/scripting an application and to
write domain specific languages (DSL):

http://micheles.googlecode.com/hg/plac/doc/plac_adv.html

http://micheles.googlecode.com/hg/plac/doc/plac_adv.pdf
