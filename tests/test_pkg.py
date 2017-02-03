# -*- coding: utf-8 -*-
import unittest
from nose.tools import *   # noqa
from unittest.mock import *  # noqa
import clique


class TestPackage(unittest.TestCase):

    def test_metadata(self):
        assert(clique.__name__)
        assert(clique.__author__)
        assert(clique.__author_email__)
        assert(clique.__version__)
        assert(clique.__version_info__)
        assert(clique.__release__)
        assert(clique.__license__)
        assert(clique.__version_txt__)

    def test_log(self):
        import logging
        from clique import log

        mylog = log.getLogger("test")
        assert(mylog.name == "test")
        assert(len(mylog.handlers) == 0)

        pkglog = log.getLogger("clique")
        assert(pkglog.name == "clique")
        assert(isinstance(pkglog.handlers[0], logging.NullHandler))

        for logger in [mylog, pkglog]:
            assert(logger.getEffectiveLevel() == logging.NOTSET)
            assert(logger.propagate)
            assert(isinstance(logger, log.Logger))

        for ll in [logging.NOTSET] + log.LEVELS:
            log.simpleConfig(ll)
            assert(pkglog.getEffectiveLevel() == ll)
            assert(len(pkglog.handlers) == 1)
            assert(isinstance(pkglog.handlers[0], logging.StreamHandler))
            assert(pkglog.handlers[0].formatter._fmt == log.LOG_FORMAT)

        assert("DEFAULT_LOGGING_CONFIG" in dir(log))

        with patch.object(pkglog, "log") as mock_log:
            pkglog.verbose("Honey's Dead")
            mock_log.assert_called_with(logging.VERBOSE, "Honey's Dead")


def test_useCliqueServer():
    from clique.keystore import RemoteKeyStore
    from clique.chainstore import RemoteChainStore

    url = "https://aliceinchains.com/clique"

    clique.useCliqueServer(url)
    assert_is_instance(clique.keystore(), RemoteKeyStore)
    assert_is_instance(clique.chainstore(), RemoteChainStore)

    class MyKeyStore(RemoteKeyStore):
        pass
    class MyChainStore(RemoteChainStore):
        pass
    clique.useCliqueServer(url, KeyStoreClass=MyKeyStore,
                           ChainStoreClass=MyChainStore)
    assert_is_instance(clique.keystore(), MyKeyStore)
    assert_is_instance(clique.chainstore(), MyChainStore)

    assert_equals(clique.keystore()._url, url + "/keys")
    assert_equals(clique.chainstore()._blocks_url, url + "/blocks")
    assert_equals(clique.chainstore()._chains_url, url + "/chains")


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

