# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import MagicMock
from nose.tools import *  # noqa
from clique.common import *  # noqa
from jwcrypto.jwk import JWK


def test_JsonType():
    jt = JsonType()
    assert_raises(NotImplementedError, jt.toJson)
    assert_raises(NotImplementedError, jt.fromJson, "data")


def test_Uri():
    x = "xmpp:trshirk@cisco.com"
    uri = Uri(x)
    assert_equal(str(uri), x)

    uri2 = Uri.create(x)
    assert_is_instance(uri2, Uri)
    assert_is_not(uri2, uri)
    assert_equal(str(uri2), x)

    uri3 = Uri.create(uri)
    assert_is_instance(uri3, Uri)
    assert_is(uri3, uri)
    assert_equal(str(uri3), x)


class TestThumbprint(unittest.TestCase):
    def setUp(self):
        k = Identity.generateKey()
        k.export = MagicMock(return_value=k.export())
        k.export_public = MagicMock(return_value=k.export_public())
        self.mocked_exports = k

        self.key = Identity.generateKey()
        self.public_key = JWK(**json.loads(self.key.export_public()))

    def test_default_key(self):
        key_json = json.loads(self.key.export())
        assert_in("d", key_json)
        assert_in("x", key_json)
        assert_in("y", key_json)
        assert_equal(key_json["kty"], "EC")
        assert_equal(key_json["size"], 256)

    def test_public_default(self):
        tp = thumbprint(self.mocked_exports)
        self.mocked_exports.export_public.assert_called_once_with()
        self.mocked_exports.export.assert_not_called()
        assert_is_not(tp, None)

    def test_base64(self):
        tp1 = thumbprint(self.key)
        tp2 = thumbprint(self.key, base64=True)
        tp3 = thumbprint(self.key, base64=False)
        assert_is_instance(tp1, str)
        assert_equal(tp1, tp2)
        assert_is_instance(tp3, bytes)

    def tearDown(self):
        pass


class TestIdentity(unittest.TestCase):
    def setUp(self):
        self.key = Identity.generateKey()
        self.ident = Identity("ident", self.key)

    def test_ctor(self):
        k = Identity.generateKey()

        i = Identity("acct", k)
        assert_equal(i.acct, "acct")
        assert_is(i.key, k)
        assert_equal(len(i.keys), 1)
        assert_is(i.keys.get(k.key_id), k)

        # No kid
        k2 = Identity.generateKey()
        del k2._params["kid"]
        assert_raises(ValueError, Identity, "acct", k2)

        # Public identity
        i3 = Identity("acct", JWK(**json.loads(Identity.generateKey()
                                                       .export_public())))
        assert_equal(len(i3.keys), 0)

    def test_toJson(self):
        # Public
        j = self.ident.toJson()
        assert_equal(j["acct"], "ident")
        assert_in("key", j)
        assert_not_in("keys", j)

        # Private
        j_priv = self.ident.toJson(private=True)
        assert_equal(j_priv["acct"], "ident")
        assert_in("key", j_priv)
        assert_in("keys", j_priv)
        assert_equal(len(j_priv["keys"]), 1)
        assert_dict_contains_subset(j_priv["key"], j_priv["keys"][0])

    def test_fromJson(self):
        # Public
        j = self.ident.toJson()
        k = Identity.fromJson(j)
        assert_dict_equal(j, k.toJson())

        # Private
        j = self.ident.toJson(private=True)
        k = Identity.fromJson(j)
        assert_dict_equal(j, k.toJson(private=True))

        # Public key in a private keychain
        del j["keys"][0]["d"]
        assert_raises(ValueError, Identity.fromJson, j)

    def test_thumbprint(self):
        assert_equal(thumbprint(self.key), self.ident.thumbprint)


class TestOrderedKeySet(unittest.TestCase):
    def setUp(self):
        self.keys = [newJwk() for _ in range(1000)]

    def test_ctor(self):
        empty = OrderedKeySet()
        assert_equal(len(empty), 0)

        filled = OrderedKeySet(keys=self.keys)
        assert_equal(len(filled), len(self.keys))

        for k in self.keys:
            assert_in(k, filled)
            assert_not_in(k, empty)

            got = filled.get(k)
            got2 = filled.get(thumbprint(k))
            assert_is(k, got)
            assert_is(k, got2)

        # Iteration of the key set is ordered
        for k1, k2 in zip(self.keys, filled):
            assert_is(k1, k2)

    def test_export(self):
        filled = OrderedKeySet(keys=self.keys)
        exported = filled.export()
        assert_is_instance(exported, str)

        exported_json = json.loads(exported)
        assert_list_equal(list(exported_json.keys()), ["keys"])
        for i, kjson in enumerate(exported_json["keys"]):
            assert_dict_equal(kjson, json.loads(self.keys[i].export()))

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
