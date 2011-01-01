default:
	make doc/plac.pdf
doc/plac.pdf: doc/plac.txt doc/plac_core.txt doc/plac_adv.txt
	cd doc; rst2pdf --footer=###Page### plac.txt; rst2html --stylesheet=$(HOME)/md/gcodedev/df.css plac.txt plac.html
upload:
	python3.1 setup.py register sdist upload 
2:
	python setup.py build; sudo python setup.py install; sudo rm -rf dist
3:
	python3.1 setup.py build; sudo python3.1 setup.py install; sudo rm -rf dist
