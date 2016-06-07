default:
	make doc/plac.pdf
doc/plac.pdf: doc/plac.rst doc/plac_core.rst doc/plac_adv.rst
	cd doc; rst2pdf --footer=###Page### plac.rst; rst2html --stylesheet=$(HOME)/plac/df.css plac.rst plac.html
upload:
	python3 setup.py register sdist upload 
2:
	python setup.py build; sudo python setup.py install; sudo rm -rf dist build
3:
	python3 setup.py install; rm -rf build dist
