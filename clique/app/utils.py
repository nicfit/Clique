# -*- coding: utf-8 -*-
_NO_VALUE = (None, None)


def prompt(prompt, default=_NO_VALUE):
    resp = _NO_VALUE
    while resp == _NO_VALUE:
        resp = input(prompt)
        if resp == '' and default != _NO_VALUE:
            resp = default
    return resp
