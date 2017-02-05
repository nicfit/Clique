import nicfit
from argparse import FileType
from .. import BlockChain, chainFactory


@nicfit.command.register
class blockchain(nicfit.Command):
    HELP = "Read blockchains."

    def _initArgParser(self, parser):
        parser.add_argument("chainfile", metavar="FILE", type=FileType('r'),
                            help="File containing serialized block chain.")

    def _run(self):
        chain_data = self.args.chainfile.read()
        chain = BlockChain.deserialize(chain_data, factory=chainFactory)
        print(chain)
