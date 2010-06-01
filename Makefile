doc/plac.pdf: doc/plac.txt
	cd doc; rst2pdf --footer=###Page### plac.txt; \
	rst2html --stylesheet=~/gcode/df.css plac.txt plac.html
upload:
	python setup.py register sdist upload 
