default:
	make doc/plac.pdf
doc/plac.pdf: doc/plac.rst doc/plac_core.rst doc/plac_adv.rst
	cd doc; rst2pdf --footer=###Page### plac.rst; rst2html --stylesheet=$(HOME)/plac/df.css plac.rst plac.html
dist:
	python3 setup.py build sdist
upload:
	python3 setup.py register sdist upload 
