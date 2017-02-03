.PHONY: clean-pyc clean-build clean-patch docs clean help lint test test-all \
        coverage docs release dist tags build clean-docs
SRC_DIRS = clique tests bin
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "clean-patch - remove patch artifacts (.rej, .orig)"
	@echo "clean-docs - remove generated doc files"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"
	@echo "build - build package source files"
	@echo ""
	@echo "Options:"
	@echo "NOSE_OPTS - If defined options added to 'nose'"
	@echo "BROWSER - Set to empty string to prevent opening docs/coverage results in a web browser"

clean: clean-build clean-pyc clean-test clean-patch clean-docs
	rm -rf tags

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage

clean-patch:
	find . -name '*.rej' -exec rm -f '{}' \;
	find . -name '*.orig' -exec rm -f '{}' \;

clean-docs:
	$(MAKE) -C docs clean

lint:
	flake8 ${SRC_DIRS}


NOSE_OPTS=--verbosity=1 --detailed-errors
test:
	nosetests $(NOSE_OPTS)

test-debug:
	nosetests -s $(NOSE_OPTS) --pdb --pdb-failures

test-all:
	tox

_COVERAGE_BUILD_D=build/tests/coverage
coverage:
	nosetests $(NOSE_OPTS) --with-coverage \
	          --cover-erase --cover-tests --cover-inclusive \
		  --cover-package=clique \
		  --cover-branches --cover-html \
		  --cover-html-dir=$(_COVERAGE_BUILD_D) tests
	@if test -n '$(BROWSER)'; then \
	    $(BROWSER) $(_COVERAGE_BUILD_D)/index.html;\
	fi

docs:
	rm -f docs/authchain.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ clique
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	@if test -n '$(BROWSER)'; then \
	    $(BROWSER) docs/_build/html/index.html;\
	fi

servedocs: docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

build:
	python setup.py build

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python setup.py install

tags:
	ctags -R ${SRC_DIRS}
