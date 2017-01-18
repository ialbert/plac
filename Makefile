.PHONY: default

default:
	make doc/plac.pdf doc/plac.html
doc/plac.pdf: doc/plac.rst doc/plac_core.rst doc/plac_adv.rst
	cd doc; rst2pdf --footer=###Page### plac.rst
doc/plac.html:
	cd doc; rst2html.py --stylesheet=../df.css plac.rst plac.html
dist:
	python3 setup.py build sdist bdist_wheel
upload:
	python3 setup.py register sdist bdist_wheel upload
