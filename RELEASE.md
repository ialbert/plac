How to make a new release
=========================

1. Update the changelog (CHANGES.md)
2. Update the version number in plac.py and doc/plac_core.rst
3. Build the docs with `make`
4. Make a tag on the repo (i.e. git tag plac-1.3.0), commit and push
5. Make a source tarball with `make dist` and upload to PyPI with
   `make upload`
