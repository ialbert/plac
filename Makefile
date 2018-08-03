.PHONY: default

default:
	cd doc && rst2html.py --stylesheet=../df.css plac.rst plac.html && rst2pdf --footer=###Page### plac.rst
dist:
	python3 setup.py build sdist bdist_wheel
upload:
	python3 setup.py register sdist bdist_wheel upload
