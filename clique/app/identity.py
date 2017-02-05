# -*- coding: utf-8 -*-
import sys
import json
import argparse

import nicfit

from .. import Identity, IdentityChain
from .utils import prompt
from ..common import thumbprint, newJwk, jwkIsPrivate


@nicfit.command.register
class identity(nicfit.Command):
    HELP = "Identity and stuffs"

    def _initArgParser(self, parser):
        parser.add_argument("-i", "--identity", default=None,
                            type=argparse.FileType('r'),
                            help="File containing an Identity in JSON format.")
        parser.add_argument("-k", "--keyfile", default=None,
                            type=argparse.FileType('r'),
                            help="File containing a private JWK.")
        parser.add_argument("--iss", default=None,
                            help="Identity issuer.")

    def _run(self):
        if self.args.identity:
            ident = Identity.fromJson(json.loads(self.args.identity.read()))
        else:
            if self.args.keyfile:
                try:
                    jwk = json.loads(self.args.keyfile.read())
                    key = newJwk(**jwk)
                    if not jwkIsPrivate(key):
                        raise ValueError(
                            "Key file does not contain a private key")
                except Exception as ex:
                    print("Error loading key: " + str(ex), file=sys.stderr)
                    return 1
                key._params["kid"] = thumbprint(key)
            else:
                key = Identity.generateKey()

            iss = self.args.iss or prompt("iss? ")
            ident = Identity(iss, key)

        ident.idchain = IdentityChain.fromIdentity(ident,
                                                   ident.acct).serialize()
        print(json.dumps(ident.toJson(private=True), indent=2, sort_keys=True))

        idchain = IdentityChain.deserialize(ident.idchain)
        print("\n## IdentityChain ##:\n" + str(idchain))
