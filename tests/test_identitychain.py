# -*- coding: utf-8 -*-
import unittest
from nose.tools import *   # noqa

from clique import *    # noqa
from clique.common import *    # noqa
from clique.chainstore import *   # noqa
from clique.identitychain import *   # noqa


class TestIdentityChain(unittest.TestCase):
    def setUp(self):
        self.ident = Identity("ozzy@sabbath.org", Identity.generateKey())

    def test_Block(self):
        ident = self.ident

        block = Block(ident, None)
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_is_none(block.pkt)

        block = Block(ident, "XXX", pkt=thumbprint(ident.key))
        assert_equals(block.creator, ident.acct)
        assert_equals(block.antecedent, "XXX")
        assert_equals(block.pkt, thumbprint(ident.key))

    def test_GodBlock(self):
        ident = self.ident

        block = GenesisBlock(ident)
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_equals(block.pkt, thumbprint(ident.key))
        assert_equals(block.subject, "CLIQUE")
        assert_equals(block.payload["tid"], identitychain.CHAIN_TYPEID)

        block = GenesisBlock(ident, sub="The BJM", song="Hide and Seek")
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_equals(block.pkt, thumbprint(ident.key))
        assert_equals(block.subject, "The BJM")
        assert_equals(block.payload["song"], "Hide and Seek")
        assert_equals(block.payload["tid"], identitychain.CHAIN_TYPEID)

    def test_iss_removed_from_Block(self):
        block = Block(self.ident, "XXX", pkt=thumbprint(self.ident.key))
        assert_not_in("iss", block.toJson())

    def test_iss_not_removed_from_GodBlock(self):
        block = GenesisBlock(self.ident)
        assert_in("iss", block.toJson())

    def test_chainFactory(self):
        bchain = BlockChain(self.ident)
        bchain.addBlock(self.ident)
        bchain.addBlock(self.ident)
        bchain.addBlock(self.ident)

        ichain = IdentityChain(self.ident, self.ident.acct)
        bchain.addBlock(self.ident, pkt=thumbprint(self.ident.rotateKey()))
        bchain.addBlock(self.ident, pkt=thumbprint(self.ident.rotateKey()))
        bchain.addBlock(self.ident, pkt=thumbprint(self.ident.rotateKey()))
        bchain.addBlock(self.ident, pkt=thumbprint(self.ident.rotateKey()))

        somechain = BlockChain.deserialize(bchain.serialize(),
                                           factory=chainFactory)
        someotherchain = BlockChain.deserialize(ichain.serialize(),
                                                factory=chainFactory)
        assert_is_instance(somechain, BlockChain)
        assert_not_is_instance(somechain, IdentityChain)
        assert_is_instance(someotherchain, IdentityChain)

    def test_Chain(self):
        ident = self.ident
        idchain = IdentityChain(ident, "Anton Newcombe")

        assert_true(issubclass(idchain.GodBlockType,
                               identitychain.GenesisBlock))
        assert_true(issubclass(idchain.GodBlockType,
                               identitychain.Block))
        assert_true(issubclass(idchain.BlockType, identitychain.Block))
        assert_false(issubclass(idchain.BlockType, identitychain.GenesisBlock))

        assert_equals(idchain.subject, "Anton Newcombe")
        assert_equals(idchain.creator, ident.acct)

    def test_fromIdentity(self):
        ident = self.ident
        keys = [ident.key]
        for _ in range(10):
            keys.append(ident.rotateKey())

        idchain = IdentityChain.fromIdentity(ident, "MaxC")
        assert_equal(idchain.subject, "MaxC")
        assert_equal(idchain.creator, ident.acct)

        # Tests thumbprints were tracked correctly
        sorted_pkt_order = {i: t for t, i in idchain._pkt_order.items()}
        sorted_thumbprints = [thumbprint(k) for k in keys]
        assert_list_equal(list(sorted_pkt_order.values()), sorted_thumbprints)
        # and the pkts also
        assert_list_equal([b.pkt for b in idchain], sorted_thumbprints)

        # Set the chain in the identity
        ident.idchain = idchain.serialize()
        ident_json = ident.toJson()
        assert_in("id_chain", ident_json)
        assert_equal(ident_json["id_chain"], idchain.serialize())
        assert_equal(ident_json["id_chain"], ident.idchain)

        for val in [b"somebytes", 1, IdentityChain(ident, "asdf")]:
            try:
                ident.idchain = val
            except TypeError:
                pass
            else:
                assert_false("TypeError expected")

    def test_isSameOrSubsequent(self):
        ident = self.ident
        keys = [ident.key]
        for _ in range(10):
            keys.append(ident.rotateKey())

        idchain = IdentityChain.fromIdentity(ident, "IgorC")
        for i, k in enumerate(keys):
            tp = thumbprint(k)
            for j in range(len(keys)):
                tp2 = thumbprint(keys[j])
                if j <= i:
                    assert_true(idchain.isSameOrSubsequent(tp, tp2))
                else:
                    assert_false(idchain.isSameOrSubsequent(tp, tp2))

        idchain.validate(idchain[0].hash)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
