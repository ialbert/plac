from setuptools import setup
import os.path


def require(*modules):
    """Check if the given modules are already available; if not add them to
    the dependency list."""
    deplist = []
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            deplist.append(module)
    return deplist


def getversion(fname):
    "Get the __version__ without importing plac"
    for line in open(fname):
        if line.startswith('__version__'):
            return eval(line[13:])


if __name__ == '__main__':
    setup(name='plac',
          version=getversion(
            os.path.join(os.path.dirname(__file__), 'plac.py')),
          description=('The smartest command line arguments parser '
                       'in the world'),
          long_description=open('README.md').read(),
          long_description_content_type="text/markdown",
          author='Michele Simionato',
          author_email='michele.simionato@gmail.com',
          url='https://github.com/ialbert/plac',
          license="BSD License",
          py_modules=['plac_core', 'plac_ext', 'plac_tk', 'plac'],
          scripts=['plac_runner.py'],
          install_requires=require('argparse'),
          keywords="command line arguments parser",
          platforms=["All"],
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: BSD License',
                       'Natural Language :: English',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'Topic :: Software Development :: Libraries',
                       'Topic :: Utilities'],
          zip_safe=False)
