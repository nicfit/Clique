# -*- coding: utf-8 -*-
import clique
"""
test_clique
----------------------------------

Tests for `clique` module.
"""


def test_metadata():
    assert clique.version
    assert clique.__about__.__license__
    assert clique.__about__.__project_name__
    assert clique.__about__.__author__
    assert clique.__about__.__author_email__
    assert clique.__about__.__version__
    assert clique.__about__.__version_info__
    assert clique.__about__.__release__
    assert clique.__about__.__version_txt__
