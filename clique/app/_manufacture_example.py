# -*- coding: utf-8 -*-
from clique import Identity, IdentityChain

###
# WIP: will raise NotImplemented
###

NUM_DEVICES = 10


def deviceTest(gbock_hash, chain_data):
    idchain = IdentityChain.deserialize(chain_data)
    idchain.validate(gbock_hash)
    print(idchain)

    # XXX: we don't have a true Identity yet, there is not secret key
    device_ident = Identity(idchain[0].subject, Identity.generateKey())
    idchain.addBlock(device_ident, pkt=device_ident.thumbprint)
    idchain.validate(gbock_hash)


def main():
    manufacturer_key = Identity.generateKey()
    manufacturer = Identity("manufacturer1", manufacturer_key)

    device_idchains = []
    for i in range(NUM_DEVICES):
        idchain = IdentityChain(manufacturer, "device{:d}".format(i))
        device_idchains.append((idchain[0].hash, idchain))

    for h, c in device_idchains:
        c.validate(h)

    for i in range(NUM_DEVICES):
        deviceTest(device_idchains[i][0], device_idchains[i][1].serialize())


if __name__ == "__main__":
    main()
