.PHONY: default

default:
	sphinx-build doc docs
dist:
	python3 setup.py build sdist bdist_wheel
upload:
	python3 setup.py register sdist bdist_wheel upload
