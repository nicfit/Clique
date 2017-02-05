# -*- coding: utf-8 -*-
from nicfit import getLogger
from .__about__ import __version__ as version                         # noqa
from .common import Identity                                          # noqa
from .blockchain import BlockChain                                    # noqa
from .authchain import Chain as AuthChain                             # noqa
from .keystore import keystore, KeyNotFoundError                      # noqa
from .chainstore import chainstore, ChainNotFoundError                # noqa
from .identitychain import Chain as IdentityChain                     # noqa
from . import blockchain, identitychain, authchain                    # noqa

log = getLogger(__package__)


def chainFactory(godblock, serialization):
    chain_types = {"identity_XXX": IdentityChain,
                   "auth_XXX": AuthChain,
                  }
    if "tid" in godblock.payload and godblock.payload["tid"] in chain_types:
        return chain_types[godblock.payload["tid"]].deserialize(serialization)


def useCliqueServer(url, KeyStoreClass=None, ChainStoreClass=None):
    from .keystore import setKeyStore, RemoteKeyStore
    from .chainstore import setChainStore, RemoteChainStore

    KeyStoreClass = KeyStoreClass or RemoteKeyStore
    ChainStoreClass = ChainStoreClass or RemoteChainStore

    setChainStore(ChainStoreClass(url))
    setKeyStore(KeyStoreClass(url + "/keys"))
