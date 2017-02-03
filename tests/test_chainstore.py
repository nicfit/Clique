# -*- coding: utf-8 -*-
import unittest
from unittest.mock import *  # noqa
from nose.tools import *  # noqa

from clique import *  # noqa
from clique.chainstore import *  # noqa


def test_ChainStore():
    from clique.chainstore import (chainstore, LocalChainStore,
                                   _global_chainstore)
    cstore = LocalChainStore()
    singleton = chainstore()
    assert_is_not(cstore, singleton)
    assert_is(singleton, _global_chainstore)

    ident = Identity("acct:catherine", Identity.generateKey())
    c1 = IdentityChain(ident, "s1")
    cstore.add(c1)
    c2 = IdentityChain(ident, "s2")
    cstore.add(c2)
    c3 = IdentityChain(ident, "s3")
    cstore.add(c3)
    c4 = IdentityChain(ident, "s4")
    cstore.add(c4)

    assert_is(cstore["s4"], c4)
    assert_is(cstore["s1"], c1)
    assert_is(cstore["s2"], c2)
    assert_is(cstore["s3"], c3)

    assert_raises(ValueError, cstore.add, c3)

    # Upload on a local chain store results on an 'add'
    cstore = LocalChainStore()
    cstore.add = MagicMock()
    cstore.upload(c3)
    cstore.add.assert_called_with(c3)


def test_global_ChainStore():
    assert_true(isinstance(chainstore(), LocalChainStore))

    class NewChainStore(LocalChainStore):
        pass
    curr = setChainStore(NewChainStore())
    assert_true(isinstance(chainstore(), NewChainStore))
    assert_true(isinstance(curr, LocalChainStore))


def test_ChainNotFoundError():
    ex = ChainNotFoundError("this is a test")
    assert_equals(str(ex), "Block chain not found: this is a test")




class Response:
    """Dummy 'requests' responce class."""
    def __init__(self, code, chain):
        self.status_code = code
        self._chain = chain

    def json(self):
        return json.loads(self._chain.serialize())


class TestRemoteChainStore(unittest.TestCase):

    def setUp(self):
        self.url = "http://chainstore.com"
        self.headers = {"content-type": "application/jose"}
        self.cs = RemoteChainStore(self.url)
        self.cs._post = MagicMock()
        # This should NOT be called when we add chains
        self.cs._post.side_effect = NotImplementedError

        chains = []
        for i in range(10):
            ident = Identity("ident{:d}".format(i), Identity.generateKey())
            ident.rotateKey()
            chain = IdentityChain.fromIdentity(ident, ident.acct)
            chains.append(chain)
        self.chains = chains

    def test_ctor(self):
        url = self.url
        h = self.headers
        cs = RemoteChainStore(url)
        assert_equals(cs._blocks_url, url + "/blocks")
        assert_equals(cs._chains_url, url + "/chains")


    def test_NoGetForCachedValues(self):
        cs = RemoteChainStore(self.url)
        cs._get = MagicMock(return_value=True)
        cs._post = MagicMock(return_value=True)
        for c in self.chains:
            cs.add(c)

        for chain, subj in [(c, c.subject) for c in self.chains]:
            c = cs[subj]
            assert_is(c, chain)
            # Should not have hit server, k is in cache
            cs._get.assert_not_called()

    def test_upload(self):
        chain = self.chains[0]
        success = Response(201, chain)
        fail = Response(500, None)

        # Happy path
        self.cs._post = MagicMock(return_value=success)
        self.cs.upload(chain)
        post_calls = []
        for block in chain:
            post_calls.append(call(self.cs._blocks_url,
                                   headers={"content-type": "application/jose"},
                                   data=block.serialize()))
        self.cs._post.assert_has_calls(post_calls)

        # Http error
        self.cs._post = MagicMock(return_value=fail)
        assert_raises(requests.RequestException, self.cs.upload, self.chains[2])

    def test_getKey(self):
        chain = self.chains[3]
        self.cs._get = MagicMock(return_value=Response(200, chain))

        c = self.cs[chain.subject]
        self.cs._get.assert_called_with(self.url + "/chains/" + chain.subject)

        self.cs._get.reset_mock()
        assert_is(self.cs[c.subject], c)
        self.cs._get.assert_not_called()

        err_chain = self.chains[4]
        self.cs._get = MagicMock(return_value=Response(500, err_chain))
        assert_raises(ChainNotFoundError,
                      self.cs.__getitem__, err_chain.subject)
