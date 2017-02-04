# -*- coding: utf-8 -*-
from nicfit import Application
from . import version


def main(args):
    print("\m/")


app = Application(main, version=version)
if __name__ == "__main__":
    app.run()
