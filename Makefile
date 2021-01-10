.PHONY: default

default:
	sphinx-build doc docs

dist: plac_core.py plac_ext.py
	python setup.py build sdist bdist_wheel

upload:
	rm -rf build/* dist/*
	python setup.py sdist bdist_wheel
	python -m twine upload --repository pypi dist/*
