# -*- coding: utf-8 -*-
from collections import namedtuple


__project_name__ = 'clique'
__project_slug__ = 'clique'
__author__ = 'Travis Shirk'
__author_email__ = 'trshirk@cisco.com'
__url__ = 'https://cliquey.io/'
__description__ = 'Cliques for Python'

__version__ = '0.2.0'
__release__ = __version__.split('-')[1] if '-' in __version__ else "final"
__version_info__ = \
    namedtuple("Version", "major, minor, maint, release")(
        *(tuple((int(v) for v in __version__.split('-')[0].split('.'))) +
          tuple((__release__,))))

__years__ = "2016"
__license__ = 'GPL'

__version_txt__ = """
%(__name__)s %(__version__)s (C) Copyright %(__years__)s %(__author__)s
This program comes with ABSOLUTELY NO WARRANTY! See LICENSE for details.
Run with --help/-h for usage information or read the docs at
%(__url__)s
""" % (locals())


from . import log                                                     # noqa
from .common import Identity                                          # noqa
from .blockchain import BlockChain                                    # noqa
from .authchain import Chain as AuthChain                             # noqa
from .keystore import keystore, KeyNotFoundError                      # noqa
from .chainstore import chainstore, ChainNotFoundError                # noqa
from .identitychain import Chain as IdentityChain                     # noqa
from . import blockchain, identitychain, authchain                    # noqa


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
