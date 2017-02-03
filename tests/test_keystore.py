# -*- coding: utf-8 -*-
import unittest
from unittest.mock import *  # noqa
from nose.tools import *  # noqa
import jwcrypto.jws

from clique.blockchain import *  # noqa
from clique.keystore import *  # noqa


def test_global_KeyStore():
    assert_true(isinstance(keystore(), LocalKeyStore))

    class NewKeyStore(LocalKeyStore):
        pass
    curr = setKeyStore(NewKeyStore())
    assert_true(isinstance(keystore(), NewKeyStore))
    assert_true(isinstance(curr, LocalKeyStore))


def test_LocalKeyStore():
    ks = LocalKeyStore()

    k1 = Identity.generateKey()
    ks.add(k1)
    assert_is(ks[thumbprint(k1)], k1)

    k2 = Identity.generateKey()
    assert_raises(KeyNotFoundError, ks.__getitem__, thumbprint(k2))
    ks.add(k2)
    assert_is(ks[thumbprint(k2)], k2)

    assert_in(thumbprint(k1), ks)
    assert_in(thumbprint(k2), ks)
    assert_not_in(thumbprint(newJwk()), ks)

    # Upload on a local key store results on an 'add'
    ks = LocalKeyStore()
    ks.add = MagicMock()
    ks.upload(k1)
    ks.add.assert_called_with(k1)

def test_KeyNotFoundError():
    ex = KeyNotFoundError("this is a test")
    assert_equals(str(ex), "Encrypion key not found: this is a test")


class Response:
    """Dummy 'requests' responce class."""
    def __init__(self, c, k):
        self.status_code = c
        self._key = k

    def json(self):
        return json.loads(self._key.export())


class TestRemoteKeyStore(unittest.TestCase):

    def setUp(self):
        self.url = "http://keystore.com/keys"
        self.headers = {"content-type": "application/json"}
        self.ks = RemoteKeyStore(self.url)
        self.ks._post = MagicMock()
        # This should NOT be called when we add keys
        self.ks._post.side_effect = NotImplementedError

        self.keys = []
        for _ in range(10):
            k = newJwk()
            self.keys.append(k)
            self.ks.add(k)


    def test_ctor(self):
        url = self.url
        h = self.headers
        ks = RemoteKeyStore(url)
        assert_equals(ks._url, url)
        assert_dict_equal(ks._headers, h)

    def test_NoGetForCachedValues(self):
        ks = RemoteKeyStore(self.url)
        ks._get = MagicMock(return_value=True)
        ks._post = MagicMock(return_value=True)
        keys = []
        for _ in range(10):
            k = newJwk()
            keys.append(k)
            ks.add(k)

        for key, tp in [(k, thumbprint(k)) for k in keys]:
            k = ks[tp]
            assert_is(k, key)
            # Should not have hit server, k is in cache
            ks._get.assert_not_called()

    def test_upload(self):
        key = self.keys[0]
        success = Response(201, key)
        fail = Response(500, None)

        # Happy path
        self.ks._post = MagicMock(return_value=success)
        tprint = self.ks.upload(key)
        self.ks._post.assert_called_with(self.url, headers=self.headers,
                                         json=json.loads(key.export_public()))
        assert_equals(tprint, thumbprint(key))

        # Http error
        self.ks._post = MagicMock(return_value=fail)
        assert_raises(requests.RequestException, self.ks.upload, self.keys[2])

        # Kid changed error
        key = self.keys[3]
        key._params["kid"] = "The Black Ryder"
        success = Response(201, key)
        self.ks._post = MagicMock(return_value=success)
        assert_raises(ValueError, self.ks.upload, key)

    def test_getKey(self):
        new_key = newJwk()
        self.ks._get = MagicMock(return_value=Response(200, new_key))

        k = self.ks[thumbprint(new_key)]
        self.ks._get.assert_called_with(self.url + "/" + thumbprint(new_key))

        self.ks._get.reset_mock()
        assert_is(self.ks[thumbprint(k)], k)
        self.ks._get.assert_not_called()

        new_key = newJwk()
        self.ks._get = MagicMock(return_value=Response(500, new_key))
        assert_raises(KeyNotFoundError,
                        self.ks.__getitem__, thumbprint(new_key))

