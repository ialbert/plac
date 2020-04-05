.PHONY: default

default:
	sphinx-build doc docs
dist: plac_core.py plac_ext.py
	python3 setup.py build sdist bdist_wheel
upload:
	rm -rf build/* dist/*
	python3 setup.py register sdist bdist_wheel upload
