# -*- coding: utf-8 -*-
import json
import requests
from abc import ABCMeta, abstractmethod

from . import getLogger
from .blockchain import BlockChain

log = getLogger(__name__)


class ChainNotFoundError(Exception):
    def __str__(self):
        return "Block chain not found: " + self.args[0]


class ChainStoreABC(metaclass=ABCMeta):
    """Abstract base for BlockChain stores."""
    @abstractmethod
    def add(self, blockchain):
        pass                                                 # pragma: no cover

    @abstractmethod
    def __getitem__(self, subject):
        pass                                                 # pragma: no cover

    def upload(self, chain):
        self.add(chain)


class LocalChainStore(ChainStoreABC):
    def __init__(self):
        self._chains = {}

    def add(self, blockchain):
        if blockchain.subject in self._chains:
            raise ValueError("Chain {} already set".format(blockchain.subject))
        self._chains[blockchain.subject] = blockchain

    def __getitem__(self, subject):
        try:
            return self._chains[subject]
        except KeyError:
            raise ChainNotFoundError(subject)

    def clear(self):
        self._chains = {}


_global_chainstore = LocalChainStore()


def chainstore():
    global _global_chainstore
    return _global_chainstore


def setChainStore(chainstore):
    global _global_chainstore
    curr = _global_chainstore
    _global_chainstore = chainstore
    return curr


class RemoteChainStore(LocalChainStore):
    def __init__(self, url):
        self._blocks_url = url + "/blocks"
        self._chains_url = url + "/chains"
        super().__init__()

    def _post(self, url, headers=None, json=None):  # pragma: no cover
        resp = requests.post(url, headers=headers, json=json, timeout=5)
        return resp

    def _get(self, url, headers=None):  # pragma: no cover
        resp = requests.get(url, timeout=5)
        return resp

    def __getitem__(self, subject):
        from . import chainFactory

        try:
            return super().__getitem__(subject)
        except ChainNotFoundError:
            resp = self._get(self._chains_url + "/" + subject)
            if resp.status_code != 200:
                log.error(resp)
                raise

            chain_data = json.dumps(resp.json())
            chain = BlockChain.deserialize(chain_data, factory=chainFactory)
            self.add(chain)
            return chain

    def upload(self, chain):
        headers = {"content-type": "application/jose"}
        for block in chain:
            resp = self._post(self._blocks_url, headers=headers,
                              data=block.serialize())
            if resp.status_code != 201:
                log.error(resp)
                raise requests.RequestException(response=resp)
        self.add(chain)
