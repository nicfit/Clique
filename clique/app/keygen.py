# -*- coding: utf-8 -*-
import json
import nicfit
from pathlib import Path
from .utils import prompt
from ..common import thumbprint, CLIQUE_D
from .. import Identity, keystore

DEFAULT_KEYFILE = None


@nicfit.command.register
class keygen(nicfit.Command):
    HELP = "Generate Clique (i.e. EC 256) encryption keys."

    def _initArgParser(self, parser):
        global DEFAULT_KEYFILE
        DEFAULT_KEYFILE = CLIQUE_D / "key"

        parser.add_argument(
            "-f", dest="ofile", default=None, metavar="output_file",
            help="Output file for public (.pub) and private key.")
        parser.add_argument(
            "-c", "--comment", default=None,
            help="An optional comment to include in the key.")
        parser.add_argument(
            "--compact", action="store_true",
            help="Output the keys in compact format.")

    def _run(self):
        keyfile = self.args.ofile or \
                    prompt("Enter file in which to save the key ({}): "
                           .format(DEFAULT_KEYFILE), default=DEFAULT_KEYFILE)
        keyfile = Path(keyfile).expanduser()
        if keyfile.exists():
            print("{} already exists.".format(keyfile))
            if prompt("Overwrite (y/n)? ") != "y":
                return 0
        keyfile_pub = Path(str(keyfile) + ".pub")

        indent = 2 if not self.args.compact else None

        print("Generating public/private P256 key pair.")
        jwk = Identity.generateKey()

        # TODO: Adding comments needs to be supported natively else it is too
        # easy to lose them along the way.
        '''
        cmt = self.args.comment or prompt("Comment (optional): ", default=None)
        if cmt:
            jwk._params["cmt"] = cmt
        prv_json = json.loads(jwk.export())
        pub_json = json.loads(jwk.export_public())
        if cmt:
            prv_json["cmt"] = pub_json["cmt"] = cmt
        '''

        for kfile, kstr in [(keyfile, jwk.export()),
                            (keyfile_pub, jwk.export_public())]:
            with open(str(kfile), "w") as fp:
                fp.write(json.dumps(json.loads(kstr), indent=indent,
                                    sort_keys=True))
                fp.write("\n")
        print("Your private key have been saved in {}".format(keyfile))
        print("Your public key have been saved in {}".format(keyfile_pub))

        if self.args.server:
            print("## Uploading public key to " + self.args.server)
            tprint = keystore().upload(jwk)
            print("## Key URL: {}/keys/{}".format(self.args.server, tprint))

        print("The key fingerprint is:\n{}".format(thumbprint(jwk)))
