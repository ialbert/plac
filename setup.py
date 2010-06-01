try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os.path
import plac

if __name__ == '__main__':
    setup(name=plac.__name__,
          version=plac.__version__,
          description='The easiest command line arguments parser in the world',
          long_description=open('README.txt').read(),
          author='Michele Simionato',
          author_email='michele.simionato@gmail.com',
          url='http://pypi.python.org/pypi/plac',
          license="BSD License",
          py_modules = ['plac'],
          install_requires=['argparse>=1.1'],
          keywords="command line arguments parser",
          platforms=["All"],
          classifiers=['Development Status :: 3 - Alpha',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: BSD License',
                       'Natural Language :: English',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Topic :: Software Development :: Libraries',
                       'Topic :: Utilities'],
          zip_safe=False)
