================
Clique python
================

Python API for ``Clique`` block chains.

Requirements
------------

* Python >= 3.4
* cryptography
* jwcrypto

Getting Started
----------------

.. code-block:: bash

    # Note, replace <username> with your own.
    $ git clone https://<username>@stash-eng-chn-sjc1.cisco.com/stash/scm/~adb/clique.git
    $ cd clique/python3

    # Using mkvirtualenv
    $ mkvirtualenv -p python3 -r requirements/default.txt clique

    # ... or virtualenv
    $ virtualenv -p python3 /path/clique
    $ source /path/clique/bin/activate
    $ pip install -r requirements/default.txt


Installation
------------
The install the ``clique`` module and scripts, either system-wide or in a
virtualenv, use ``setup.py`` in the standard fashion. 

.. code-block:: bash

    # To install
    $ ./setup.py install
    $ bin/example.py

.. note::
   Developers should skip the install since testing requires pushing new
   versions. See the developer section.


Development
-----------

To initialize the environment to run against your working copy use the
``develop`` command.

.. code-block:: bash

    # To develop 
    $ ./setup.py develop
    $ bin/example.py

For running tests and performing other developer tasks more dependencies are
required.

.. code-block:: bash

    # For running tests
    $ pip install -r requirements/test.txt

    # For running tests with coverage, tox, building docs, linting, etc
    $ pip install -r requirements/develop.txt

The top-level ``Makefile`` contains may common development tasks.

.. code-block:: bash

    $ make help
    clean - remove all build, test, coverage and Python artifacts
    clean-build - remove build artifacts
    clean-pyc - remove Python file artifacts
    clean-test - remove test and coverage artifacts
    clean-patch - remove patch artifacts (.rej, .orig)
    lint - check style with flake8
    test - run tests quickly with the default Python
    test-all - run tests on every Python version with tox
    coverage - check code coverage quickly with the default Python
    docs - generate Sphinx HTML documentation, including API docs
    release - package and upload a release
    dist - package
    install - install the package to the active Python's site-packages
    build - build package source files

    Options:
    TEST_PDB - If defined PDB options are added when 'nose' is invoked
    BROWSER - Set to empty string to prevent opening docs/coverage results in a web browser
