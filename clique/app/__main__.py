# -*- coding: utf-8 -*-
import sys
import json
import logging
from pathlib import Path
from argparse import FileType, RawDescriptionHelpFormatter

from .args import ArgumentParser
from ..log import simpleConfig, log
from .. import KeyNotFoundError, useCliqueServer

clique_env = \
    {
        "CLIQUE_D": Path("~/.clique").expanduser(),
    }


def blockchain(args):
    from .. import BlockChain, chainFactory
    chain_data = args.chainfile.read()
    chain = BlockChain.deserialize(chain_data, factory=chainFactory)
    print(chain)


def main(args):
    log.debug("Args: {}".format(args))

    if "func" in args:
        return args.func(args)
    else:
        print("Noting to do, see --help")
        return 1


EPILOG = \
"""Examples:
  %(prog)s keygen                       # to generate a key.
  %(prog)s identity                     # to generate a identity.
  %(prog)s --server=url keygen          # to generate a identity and upload it.

Use '%(prog)s <subcmd> --help' for detailed info about a particular command.
"""  # noqa


def _argsParser():
    arg_parser = ArgumentParser(prog="clique", add_log_args=True, epilog=EPILOG,
                                formatter_class=RawDescriptionHelpFormatter)
    arg_parser.add_argument("--server", metavar="URL",
                            help="URL of remote key server.")
    sub_parser = arg_parser.add_subparsers(title="Subcommands", dest="subcmd")

    # keygen
    from . import keygen
    cmd_parser = keygen.init(clique_env, sub_parser)
    cmd_parser.set_defaults(func=keygen.run)

    # identity
    from . import identity
    cmd_parser = identity.init(clique_env, sub_parser)
    cmd_parser.set_defaults(func=identity.run)

    # blockchain
    blockchain_parser = sub_parser.add_parser("blockchain",
                                              help="Read blockchains.")
    blockchain_parser.add_argument("chainfile", metavar="FILE",
            type=FileType('r'),
            help="File containing serialized block chain.")
    blockchain_parser.set_defaults(func=blockchain)

    contract_parser = sub_parser.add_parser("contract_example", help="Toy")
    contract_parser.set_defaults(func=contract_example)

    return arg_parser


def contract_example(_):
    from uuid import uuid4
    import requests
    from clique.blockchain import BlockChain, Block, Identity
    from clique import keystore

    ipecac = Identity("label:Ipecac", Identity.generateKey())
    patton = Identity("artist:Mike Patton", Identity.generateKey())
    melvins = Identity("artist:Melvins", Identity.generateKey())
    fantômas = Identity("artist:Fantômas", Identity.generateKey())
    buzzo = Identity("artist:King Buzzo", Identity.generateKey())
    unsane = Identity("artist:Unsane", Identity.generateKey())
    fnm = Identity("artist:Faith No More", Identity.generateKey())
    for k in [i.key for i in [ipecac, patton, melvins, fantômas, buzzo,
                              unsane, fnm]]:
        keystore().upload(k)

    c = BlockChain(ipecac)
    godblock = c.addBlock(ipecac,
                          sub="Ipecac recording artists: " + str(uuid4()),
                          tid="GOD")
    godblock.verify(ipecac.key)
    contract = c.addBlock(patton, thing="contract", blahblah="....")
    contract.verify(patton.key)
    # Multiple signers
    c.addBlock(fantômas, thing="contract", blahblah="....")
    # XXX: Multi signing not yet suported
    '''
    fantômas_contract.sign(patton.key)
    fantômas_contract.sign(melvins.key)
    fantômas_contract.sign(buzzo.key)
    '''

    print(c)
    GHASH = godblock.hash

    ######################################################
    CONTRACT_BLOCK_CHAIN = c.serialize()
    print(CONTRACT_BLOCK_CHAIN)

    ipecac_contracts = BlockChain.deserialize(CONTRACT_BLOCK_CHAIN)
    ipecac_contracts.addBlock(buzzo, thing="contract", blahblah="....")
    ipecac_contracts.addBlock(melvins, thing="contract", blahblah="....")

    NEW_CHAIN = ipecac_contracts.serialize()
    for new_block in ipecac_contracts[-2:]:
        # upload to block server, for example
        pass

    ######################################################
    download = NEW_CHAIN
    melvins_crew = BlockChain.deserialize(download)
    melvins_crew.validate(GHASH)
    print(melvins_crew)
    # += instead of addBlock, antecedents are computed as whith addBlock
    melvins_crew += Block(ipecac, None, ack=True,
                          ptk="FIXME: get fprint from block being acked")
    melvins_crew += Block(ipecac, None, ack=True,
                          ptk="FIXME: get fprint from block being acked")
    print(melvins_crew)
    CONTRACT_BLOCK_CHAIN = melvins_crew.serialize()

    master = BlockChain.deserialize(CONTRACT_BLOCK_CHAIN)
    master.addBlock(ipecac, thing="contract:offer", new_signing="Unsane",
                    blahblah="....")
    master.addBlock(ipecac, thing="contract:offer", new_signing="Faith No More",
                    blahblah="....")
    CONTRACT_BLOCK_CHAIN = master.serialize()

    ######################################################
    download = CONTRACT_BLOCK_CHAIN
    fnm_offer = BlockChain.deserialize(download)
    print(fnm_offer)
    fnm_offer.validate(GHASH)
    fnm_offer.addBlock(fnm, ack=False)
    deny_upload = fnm_offer.serialize()

    #####################################################
    download = CONTRACT_BLOCK_CHAIN
    unsane_offer = BlockChain.deserialize(download)
    print(unsane_offer)
    unsane_offer.validate(GHASH)
    unsane_offer.addBlock(unsane, ack=True)
    accept_upload = unsane_offer.serialize()

    ######################################################

    yes_from_unsane = BlockChain.deserialize(accept_upload)
    yes_from_unsane.validate(GHASH)
    no_from_ftm = BlockChain.deserialize(deny_upload)
    yes_from_unsane.validate(GHASH)

    # XXX: at this point there is a merge op
    print(yes_from_unsane)
    print(no_from_ftm)

    with open("sample.json", "w") as fp:
        fp.write(CONTRACT_BLOCK_CHAIN)

    if args.server:
        h = {"content-type": "application/jose"}
        new_chain = BlockChain.deserialize(CONTRACT_BLOCK_CHAIN)
        for block in new_chain:
            print("UPLOADING:", block)
            resp = requests.post(args.server + "/blocks", headers=h,
                                 data=block.serialize(),
                                 timeout=5)
            if resp.status_code != 201:
                log.error(resp)
                raise requests.RequestException(response=resp)

        resp = requests.get(args.server + "/chains/" +
                            new_chain[0].payload["sub"])
        downloaded_chain = BlockChain.deserialize(json.dumps(resp.json()))
        downloaded_chain.validate(new_chain[0].hash)


if __name__ == "__main__":
    simpleConfig(logging.WARN)
    arg_parser = _argsParser()

    try:
        args = arg_parser.parse_args()
        if args.server:
            useCliqueServer(args.server)
    except Exception as ex:
        arg_parser.error(str(ex))  # does not return

    try:
        sys.exit(main(args) or 0)
    except KeyNotFoundError as ex:
        print(str(ex), file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(0)
