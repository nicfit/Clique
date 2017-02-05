==============
Clique Python
==============

Python API for Clique block chains; ID chains and auth chains included.

Invented by Andrew Biggs <balthorium@gmail.com>, and contributed to by others.

Status
------
.. image:: https://img.shields.io/pypi/v/clique-blockchain.svg
   :target: https://pypi.python.org/pypi/clique-blockchain/
   :alt: Latest Version
.. image:: https://img.shields.io/pypi/status/clique-blockchain.svg
   :target: https://pypi.python.org/pypi/clique-blockchain/
   :alt: Project Status
.. image:: https://travis-ci.org/nicfit/Clique.svg?branch=master
   :target: https://travis-ci.org/nicfit/Clique
   :alt: Build Status
.. image:: https://img.shields.io/pypi/l/clique-blockchain.svg
   :target: https://pypi.python.org/pypi/clique-blockchain/
   :alt: License
.. image:: https://img.shields.io/pypi/pyversions/clique-blockchain.svg
   :target: https://pypi.python.org/pypi/clique-blockchain/
   :alt: Supported Python versions
.. image:: https://coveralls.io/repos/nicfit/Clique/badge.svg
   :target: https://coveralls.io/r/nicfit/Clique
   :alt: Coverage Status

Features
--------


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
    $ clique examples authchain

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
    $ clique examples authchain

For running tests and performing other developer tasks more dependencies are
required.

.. code-block:: bash

    # For running tests
    $ pip install -r requirements/test.txt

    # For running tests with coverage, tox, building docs, linting, etc
    $ pip install -r requirements/dev.txt
