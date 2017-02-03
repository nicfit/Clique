# -*- coding: utf-8 -*-
import sys
import json
import argparse

from .. import Identity, IdentityChain
from .utils import prompt
from ..common import thumbprint, newJwk, jwkIsPrivate


def init(clique_env, cmd_parser):
    parser = cmd_parser.add_parser("identity", help="Identity stuffs")
    parser.add_argument("-i", "--identity", default=None,
                        type=argparse.FileType('r'),
                        help="File containing an Identity in JSON format.")
    parser.add_argument("-k", "--keyfile", default=None,
                        type=argparse.FileType('r'),
                        help="File containing a private JWK.")
    parser.add_argument("--iss", default=None,
                        help="Identity issuer.")
    return parser


def run(args):
    if args.identity:
        ident = Identity.fromJson(json.loads(args.identity.read()))
    else:
        if args.keyfile:
            try:
                jwk = json.loads(args.keyfile.read())
                key = newJwk(**jwk)
                if not jwkIsPrivate(key):
                    raise ValueError("Key file does not contain a private key")
            except Exception as ex:
                print("Error loading key: " + str(ex), file=sys.stderr)
                return 1
            key._params["kid"] = thumbprint(key)
        else:
            key = Identity.generateKey()

        iss = args.iss or prompt("iss? ")
        ident = Identity(iss, key)

    ident.idchain = IdentityChain.fromIdentity(ident, ident.acct).serialize()
    print(json.dumps(ident.toJson(private=True), indent=2, sort_keys=True))

    idchain = IdentityChain.deserialize(ident.idchain)
    print("\n## IdentityChain ##:\n" + str(idchain))
