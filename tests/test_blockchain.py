# -*- coding: utf-8 -*-
import unittest
from unittest.mock import *  # noqa
from nose.tools import *  # noqa
import jwcrypto.jws

from clique.blockchain import *  # noqa
from clique.keystore import *  # noqa


class TestBlockChain(unittest.TestCase):
    def setUp(self):
        key = self.key = Identity.generateKey()
        ident = self.ident = Identity("uncleacid@deadbeats.com", key)

    def test_Serialization(self):
        chain = BlockChain()
        chain.addBlock(self.ident)
        chain.addBlock(self.ident)
        chain.addBlock(self.ident, **{"band": "Talking Heads"})
        chain.addBlock(self.ident, **{"pi": 3.14, "N": 42})
        chain.addBlock(self.ident, e=2.718281828459, X=14)
        chain.addBlock(self.ident, sub="scrobble",
                       artist="Watain", title="From the Pulpits of Abomination",
                       length=400)
        chain.validate(chain[0].hash)

        serialized = chain.serialize()

        chain2 = BlockChain.deserialize(serialized)
        chain2.validate(chain[0].hash)

        assert_equals(len(chain), len(chain2))
        for c1b, c2b in zip(chain, chain2):
            assert_equals(c1b.antecedent, c2b.antecedent)
            assert_equals(c1b.hash, c2b.hash)
            assert_dict_equal(dict(c1b.payload), dict(c2b.payload))

            c1b.verify()
            c2b.verify()

            new_key = Identity.generateKey()
            assert_raises(jwcrypto.jws.InvalidJWSSignature, c2b.verify, new_key)

    def test_ctor(self):
        chain = BlockChain()
        assert_is(chain.BlockType, Block)
        assert_is(chain.GodBlockType, Block)
        assert_equals(len(chain._blocks), 0)

        chain = BlockChain()
        try:
            b = chain.genesis_block
            assert_is_not(b, None)
        except IndexError:
            pass
        else:
            assert_false("Expected IndexError")

    def test_addBlock(self):
        class GodBlock(Block):
            def __init__(self, ident):
                super().__init__(ident, None)

        class NewChain(BlockChain):
            GodBlockType = GodBlock

        chain = NewChain()
        chain._newBlock = MagicMock(return_value=None)

        # Block 0
        block0 = chain.addBlock(self.ident)
        chain._newBlock.assert_called_with(block0)

        assert_is(chain.genesis_block, chain[0])
        assert_is(chain.genesis_block, block0)
        assert_is_instance(chain.genesis_block, GodBlock)

        assert_is_none(block0.antecedent)
        assert_equals(block0.creator, self.ident.acct)
        assert_equals(block0.payload["iss"], self.ident.acct)

        # Block 1
        payload = {"band": "This Band in Heaven",
                   "song": "Sleazy Dreams"}
        chain.addBlock(self.ident, **payload)
        chain._newBlock.assert_called_with(chain[1])

        assert_is_instance(chain[1], Block)
        assert_dict_contains_subset(payload, chain[1].payload)
        assert_equals(chain[1].payload["iss"], self.ident.acct)

        assert_equals(chain[1].payload["ant"], chain[1].antecedent)
        assert_equals(chain[1].antecedent, block0.hash)

        chain.validate(chain[0].hash)

        assert_raises(ChainValidationError, chain.validate,
                      "8686305d62bc647ce3f1f9908efa3ab33dbe87b3")

        b1 = chain.addBlock(self.ident)
        b2 = chain.addBlock(self.ident)
        b3 = chain.addBlock(self.ident)
        # Messing wit the links
        orig_b3ant = b3.antecedent
        b3.antecedent = b2.antecedent
        assert_raises(ChainValidationError, chain.validate, chain[0].hash)
        # Restore da links
        b3.antecedent = orig_b3ant
        chain.validate(chain[0].hash)

    def test_NoneAntecedent(self):
        b = Block(self.ident, "Bolt Thrower")
        assert_equals(b.antecedent, "Bolt Thrower")
        assert_in("ant", b._payload)

        b.antecedent = None
        assert_is_none(b.antecedent)
        assert_not_in("ant", b._payload)

    def test_chainSerialize(self):
        chain = BlockChain()
        chain.addBlock(self.ident)
        chain.addBlock(self.ident, **{"band": "Talking Heads"})
        chain.addBlock(self.ident, **{"pi": 3.14, "N": 42})
        chain.addBlock(self.ident, e=2.718281828459, X=14)
        chain.addBlock(self.ident, sub="scrobble",
                       artist="Watain", title="From the Pulpits of Abomination",
                       length=400)
        chain.validate(chain[0].hash)

        # chain.serialize()
        assert_equal(json.loads(chain.serialize()),
                     [b.serialize() for b in chain])

        # chain.toJson()
        assert_equal(chain.toJson(), [b.toJson() for b in chain])

        # empty chain
        emptychain = BlockChain.deserialize("[]")
        assert_equal(len(emptychain), 0)

    def test_magic(self):
        chain = BlockChain()
        blocks = []
        for i in range(10):
            blocks.append(chain.addBlock(self.ident))

        assert_equals(len(chain), 10)
        assert_equals(blocks, [b for b in chain])
        assert_equals([b for b in reversed(blocks)],
                      [b for b in reversed(chain)])

        for i in range(10):
            assert_is(chain[i], blocks[i])

    def test_toJson(self):
        chain = BlockChain()
        payload = {"track": "Speakerbox",
                   "artist": "Outkast"}
        b = chain.addBlock(self.ident, **payload)

        assert_dict_equal(b.payload, b.toJson())
        assert_in("iss", b.toJson())
        assert_in("track", b.toJson())
        assert_in("artist", b.toJson())

        assert_not_in("artist", b.toJson(omit=["artist"]))
        assert_in("iss", b.toJson(omit=["artist", "bazz"]))
        assert_in("track", b.toJson(omit=["artist"]))

        assert_in("title", b.toJson(remap={"track": "title", "iss": "me"}))
        assert_not_in("track", b.toJson(remap={"track": "title", "iss": "me"}))
        assert_in("me", b.toJson(remap={"track": "title", "iss": "me"}))
        assert_not_in("iss", b.toJson(remap={"track": "title", "iss": "me"}))
        assert_in("artist", b.toJson(remap={"track": "title", "iss": "me"}))

        assert_in("artist", b.toJson(add={"creator": "them", "who": "me"}))
        assert_in("iss", b.toJson(add={"creator": "them", "who": "me"}))
        assert_in("track", b.toJson(add={"creator": "them", "who": "me"}))
        assert_in("creator", b.toJson(add={"creator": "them", "who": "me"}))
        assert_in("who", b.toJson(add={"creator": "them", "who": "me"}))

        assert_raises(ValueError, b.toJson, add={"iss": "H.R."})

    def test_assignAdd(self):
        chain = BlockChain()
        chain += Block(self.ident, None, foo=1, bazz="1")
        chain += Block(self.ident, chain[-1], foo=2, bazz="2")
        chain += Block(self.ident, chain[-1], foo=3, bazz="3")
        chain += Block(self.ident, chain[-1], foo=4, bazz="4")
        chain += Block(self.ident, chain[-1], foo=5, bazz="5")

        assert_equals(len(chain), 5)
        for i, b in enumerate(chain, 1):
            assert_equals(i, b.payload["foo"])
            assert_equals(str(i), b.payload["bazz"])

    def test_stringify(self):
        c1 = BlockChain()
        c1.addBlock(self.ident)
        c1.addBlock(self.ident, **{"band": "Talking Heads"})
        c1.addBlock(self.ident, **{"pi": 3.14, "N": 42})
        c1.addBlock(self.ident, e=2.718281828459, X=14)

        c2 = BlockChain.deserialize(c1.serialize())

        assert_equals(str(c1), str(c2))

def testChainValidateErrorFalseness():
    cve = ChainValidationError("Wicked World")
    assert_false(cve)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
