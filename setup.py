try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os.path

def getversion(fname):
    "Get the __version__ without importing plac"
    for line in open(fname):
        if line.startswith('__version__'):
            return eval(line[13:])

if __name__ == '__main__':
    setup(name='plac',
          version=getversion(os.path.join(os.path.dirname(__file__),'plac.py')),
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
