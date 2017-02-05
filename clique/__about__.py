# -*- coding: utf-8 -*-
from collections import namedtuple

__version__ = "0.2.3"
__release_name__ = ""
__years__ = "2016-2017"

__project_name__ = "Clique"
__project_slug__ = "clique"
__author__ = "Travis Shirk"
__author_email__ = "travis@pobox.com"
__url__ = "https://github.com/nicfit/clique"
__description__ = "Python API for Clique block chains; ID chains and auth chains included."  # noqa
__long_description__ = ""
__license__ = "GNU LGPL v3.0"
__github_url__ = "https://github.com/nicfit/clique",

__release__ = __version__.split("-")[1] if "-" in __version__ else "final"
_v = tuple((int(v) for v in __version__.split("-")[0].split(".")))
__version_info__ = \
    namedtuple("Version", "major, minor, maint, release")(
        *(_v + (tuple((0,)) * (3 - len(_v))) +
          tuple((__release__,))))
del _v
__version_txt__ = """
%(__name__)s %(__version__)s (C) Copyright %(__years__)s %(__author__)s
This program comes with ABSOLUTELY NO WARRANTY! See LICENSE for details.
Run with --help/-h for usage information or read the docs at
%(__url__)s
""" % (locals())
