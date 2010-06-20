default:
	make doc/plac.pdf; make doc/plac_adv.pdf
doc/plac.pdf: doc/plac.txt
	cd doc; rst2pdf --footer=###Page### plac.txt; rst2html --stylesheet=$(HOME)/gcode/df.css plac.txt plac.html
doc/plac_adv.pdf: doc/plac_adv.txt
	cd doc; rst2pdf --footer=###Page### plac_adv.txt; rst2html --stylesheet=$(HOME)/gcode/df.css plac_adv.txt plac_adv.html
upload:
	python3 setup.py register sdist upload 
