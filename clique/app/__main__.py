# -*- coding: utf-8 -*-
from nicfit import Application, getLogger
from argparse import RawDescriptionHelpFormatter

from ..__about__ import __version__
from .. import useCliqueServer
from . import keygen   # noqa
from . import identity  # noqa
from . import blockchain  # noqa
from . import examples  # noqa

log = getLogger(__name__)


def main(args):
    log.debug("Args: {}".format(args))

    if args.server:
        useCliqueServer(args.server)

    if args.command_func:
        return args.command_func(args)
    else:
        # XXX: not sure if you can happen anymore
        print("Noting to do, see --help")
        return 1


EPILOG = \
"""Examples:
  %(prog)s keygen                       # to generate a key.
  %(prog)s identity                     # to generate a identity.
  %(prog)s --server=url keygen          # to generate a identity and upload it.

Use '%(prog)s <subcmd> --help' for detailed info about a particular command.
"""  # noqa

argparse_opts = {"epilog": EPILOG,
                 "formatter_class": RawDescriptionHelpFormatter,
                }
app = Application(main, name="clique", version=__version__,
                  extra_arg_parser_opts=argparse_opts)
app.arg_parser.add_argument("--server", metavar="URL",
                            help="URL of remote key server.")
app.enableCommands(title="Subcommands", dest="subcmd")

if __name__ == "__main__":  # pragma: nocover
    app.run()
