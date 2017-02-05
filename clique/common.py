# -*- coding: utf-8 -*-
import json
import urllib.parse
from pathlib import Path
from collections import OrderedDict

from jwcrypto.jwk import JWK
from jwcrypto.common import base64url_encode, json_encode, json_decode

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

CLIQUE_D = Path("~/.clique").expanduser()


class Uri(urllib.parse.ParseResult):
    """A non-validation URI class."""
    def __new__(cls, uri):
        """Need to tweak the metaclass for a custom constructor of namedtuple.
        """
        uri = urllib.parse.urlparse(uri)
        return super(cls, Uri).__new__(cls, *uri._asdict().values())

    def __init__(self, uri):
        pass

    def __str__(self):
        return urllib.parse.urlunparse(self)

    @staticmethod
    def create(uri):
        """Returns the ``uri`` if it is a ``Uri`` type, otherwise it returns a
        newly constructed object.
        """
        if not isinstance(uri, Uri):
            uri = Uri(uri)
        return uri


class JsonType(object):
    """Interface and base class for class with map to/from JSON."""

    def toJson(self):
        """Returns a JSON dict of the object."""
        raise NotImplementedError()

    @classmethod
    def fromJson(Class, data):
        """Returns an instance of the subclass initialized from ``data``.

        Args:
            data (dict): JSON dict containg object values.
        """
        raise NotImplementedError()


def thumbprint(jwk, base64=True):
    """Compute a digital thumbprint for the key ``jwk``."""
    key_dict = json.loads(jwk.export_public())
    d = OrderedDict()
    for k in ["crv", "kty", "x", "y"]:
        d[k] = key_dict[k]

    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(json.dumps(d, separators=(',', ':')).encode("utf8"))
    tp = digest.finalize()

    return base64url_encode(tp) if base64 else tp


def newJwk(**key_args):
    """Create a new JWK obkject with a 'kid' attribute that contains the
    key's thumbprint.
    """
    from .keystore import keystore

    if not key_args:
        jwk = JWK(generate="EC", size=256)
    else:
        jwk = JWK(**key_args)
    jwk._params["kid"] = thumbprint(jwk)
    keystore().add(jwk)
    return jwk


def jwkIsPrivate(jwk):
    """Returns ``True`` if the JWK contain private key material, or ``False``
    if the key is public.
    """
    try:
        return bool(jwk.get_op_key("decrypt"))
    except KeyError:
        return False


class OrderedKeySet(object):
    """A set of keys (strings) that maintains order when exported."""
    def __init__(self, keys=None):
        self._keys = OrderedDict()
        for k in (keys or []):
            self.add(k)

    def add(self, key):
        self._keys[thumbprint(key)] = key

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        for k in self._keys:
            yield self._keys[k]

    def __contains__(self, k):
        if isinstance(k, JWK):
            k = thumbprint(k)
        return k in self._keys

    def get(self, k):
        if isinstance(k, JWK):
            k = thumbprint(k)
        return self._keys[k] if k in self else None

    def export(self):
        """Exports the set using the standard JSON format"""
        keys = list()
        for jwk in self:
            keys.append(json_decode(jwk.export()))
        return json_encode({'keys': keys})


class Identity(JsonType):
    """Container for identity information for the entity identified by ``acct``.
    """

    def __init__(self, acct_uri, key, keys=None):
        """
        Args:
            acct_uri (Uri): A URI identifying the entity. A str value is
                            automatically converted to a Uri.
            key (JWK): The active key for the Identity.
            keys (List[JWK]): Other keys used by this Identity.
                Optional, with a default of None.

        Raises:
            ValueError: Thrown for key errors. e.g. a missing `kid`.
        """
        self.acct = str(Uri.create(acct_uri))

        self._key = key
        private_identity = jwkIsPrivate(key)
        if not self.key.key_id:
            raise ValueError("Active key must have a key ID (i.e. kid)")

        self.keys = OrderedKeySet(keys or [])
        if private_identity and not self.keys.get(self.key.key_id):
            self.keys.add(self.key)

        self._idchain = None

    @property
    def key(self):
        """jwcrypto.jwk.JWK: The active key.

        This MAY have a private key for a 'private' Identity, and will NOT for
        public identities.
        """
        return self._key

    @property
    def thumbprint(self):
        return thumbprint(self.key)

    @property
    def idchain(self):
        return self._idchain

    @idchain.setter
    def idchain(self, c):
        """Set a **serialized** IdentityChain."""
        if not isinstance(c, str):
            raise TypeError("IdentityChain must be serialized")
        self._idchain = c

    @staticmethod
    def generateKey():
        """Generates a 256 bit elliptic-curve keypair.
        Returns:
            JWK: The new key.
        """
        return newJwk()

    def rotateKey(self, key=None):
        if not key:
            key = Identity.generateKey()
        self.keys.add(key)
        self._key = key
        return key

    def toJson(self, private=False):
        d = {}
        d["acct"] = self.acct
        d["key"] = json.loads(self.key.export_public())
        if private:
            d["keys"] = []
            for k in self.keys:
                d["keys"].append(json.loads(k.export()))
        if self.idchain:
            d["id_chain"] = self._idchain
        return d

    @classmethod
    def fromJson(_, data):
        ident = Identity(data["acct"], newJwk(**data["key"]))
        if "keys" in data:
            # This is a private (personal) identity
            for k in data["keys"]:
                key = newJwk(**k)
                if jwkIsPrivate(key):
                    ident.keys.add(key)
                else:
                    raise ValueError("Key set values require a private key")
        return ident
