import nicfit


@nicfit.command.register
class examples(nicfit.Command):
    HELP = "Various example/demo apps."

    def _initArgParser(self, parser):
        parser.add_argument("app", choices=["authchain", "contract",
                                            "manufacturer_WIP"],
                            help="The example to run.")

    def _run(self):
        if self.args.app == "authchain":
            from . import _authchain_example
            _authchain_example.main()
        elif self.args.app == "contract":
            from . import _contract_example
            _contract_example.contract_example(self.args)
        elif self.args.app == "manufacturer_WIP":
            from . import _manufacture_example
            _manufacture_example.main()
        else:
            raise NotImplemented("This should not happen")
