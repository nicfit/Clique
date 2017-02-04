============
Installation
============

Using pip
------------
At the command line::

    $ pip install clique

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv Clique
    $ pip install clique

Using a source distribution
-----------------------------
At the command line:

.. parsed-literal::

    $ tar zxf clique-|version|.tar.gz
    $ cd clique-|version|
    $ python setup.py install
From GitHub
--------------
At the command line::
    $ git clone https://github.com/nicfit/Clique
    $ cd mishmash
    $ python setup.py install

Additional dependencies should be installed if developing MishMash::

    $ pip install -r requirements/dev.txt

Dependencies
-------------
All the required software dependencies are installed using either
``requirements/default.txt`` files or by ``python install setup.py``.
