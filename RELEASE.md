How to make a new release
=========================

1. Update the changelog (CHANGES.md)
2. Update the version number in plac.py and doc/plac_core.rst
3. Make a tag on the repo (i.e. git tag v1.3.0), commit and push
4. Make a source tarball with `make dist` and upload to PyPI with
   `make upload`
