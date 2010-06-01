doc/plac.pdf: doc/plac.txt
	cd doc; rst2pdf plac.txt; rst2html plac.txt plac.html
upload:
	python setup.py register sdist upload 
