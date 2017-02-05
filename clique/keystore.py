# -*- coding: utf-8 -*-
import json
import requests
from abc import ABCMeta, abstractmethod

from . import getLogger
from .common import thumbprint, newJwk

log = getLogger(__name__)


class KeyNotFoundError(Exception):
    def __str__(self):
        return "Encrypion key not found: " + self.args[0]


class KeyStoreABC(metaclass=ABCMeta):
    """Abstract base for JWK key stores."""
    @abstractmethod
    def add(self, jwk):
        pass                                                 # pragma: no cover

    @abstractmethod
    def __getitem__(self, tp):
        pass                                                 # pragma: no cover

    def upload(self, jwk):
        self.add(jwk)


class LocalKeyStore(KeyStoreABC):
    def __init__(self):
        self._keys = {}

    def add(self, jwk):
        tp = thumbprint(jwk)
        self._keys[tp] = jwk

    def __getitem__(self, tp):
        try:
            return self._keys[tp]
        except KeyError:
            raise KeyNotFoundError(tp)

    def __contains__(self, tp):
        return tp in self._keys


_global_keystore = LocalKeyStore()


def keystore():
    global _global_keystore
    return _global_keystore


def setKeyStore(keystore):
    global _global_keystore
    curr = _global_keystore
    _global_keystore = keystore
    return curr


class RemoteKeyStore(LocalKeyStore):
    def __init__(self, url):
        self._url = url
        self._headers = {"content-type": "application/json"}
        super().__init__()

    def add(self, jwk):
        return super().add(jwk)

    def _post(self, url, headers=None, json=None):  # pragma: no cover
        resp = requests.post(url, headers=headers, json=json, timeout=5)
        return resp

    def _get(self, url, headers=None):  # pragma: no cover
        resp = requests.get(url, timeout=5)
        return resp

    def upload(self, jwk):
        tprint = thumbprint(jwk)
        resp = self._post(self._url, headers=self._headers,
                          json=json.loads(jwk.export_public()))
        if resp.status_code != 201:
            log.error(resp)
            raise requests.RequestException(response=resp)
        elif resp.json()["kid"] != tprint:
            raise ValueError("'kid' changed on upload")
        else:
            log.debug("RemoteKeyStore.upload response: {}".format(resp.json()))
            self.add(jwk)

        return tprint

    def __getitem__(self, tp):
        try:
            return super().__getitem__(tp)
        except KeyNotFoundError:
            resp = self._get("/".join([self._url, tp]))
            if resp.status_code != 200:
                log.error(resp)
                raise
            jwk = newJwk(**resp.json())
            self.add(jwk)
            return jwk
