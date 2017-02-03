================
Clique python
================

Python API for ``Clique`` block chains; ID chains and auth chains included.

Invented by Andrew Biggs <balthorium@gmail.com>, and contributed to by others.

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
    $ pip install -r requirements/dev.txt
