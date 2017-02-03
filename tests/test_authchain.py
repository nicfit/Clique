# -*- coding: utf-8 -*-
import unittest
from unittest.mock import *  # noqa
from nose.tools import *  # noqa

from clique import *    # noqa
from clique.common import *    # noqa
from clique.authchain import *   # noqa


def testGrantTypes():
    assert_is_instance(Grant.Type.VIRAL_GRANT, Enum)
    assert_is_instance(Grant.Type.GRANT, Enum)
    assert_is_instance(Grant.Type.REVOKE, Enum)
    assert_equals(len(Grant.Type.__members__), 3)


def testGrantCtor():
    g = Grant(Grant.Type.GRANT, "participant", "Jus", "tprint")
    assert_equals(g.type, Grant.Type.GRANT)
    assert_equals(g.privilege, "participant")
    assert_equals(g.grantee, "Jus")
    assert_equals(g.thumbprint, "tprint")

    for gstr, gtype in Grant.Type.__members__.items():
        g1 = Grant(gstr, "participant", "Jus", "tprint")
        g2 = Grant(gtype, "participant", "Jus", "tprint")
        assert_equal(g1.type, g2.type)

    assert_raises(ValueError, Grant, "FOOBAZZ", "participant", "Jus", "tprint")
    assert_raises(ValueError, Grant, 1, "participant", "Jus", "tprint")


def testGrantJson():
    for gstr, gtype in Grant.Type.__members__.items():
        g = Grant(gtype, "participant", "Jus", "tprint")
        gjson = g.toJson()
        assert_dict_equal(gjson, {'grantee': 'Jus',
                                  'privilege': 'participant',
                                  'thumbprint': 'tprint',
                                  'type': gstr})
        g2 = Grant.fromJson(gjson)
        assert_dict_equal(gjson, g2.toJson())


class TestAuthChain(unittest.TestCase):
    def setUp(self):
        self.liz = Identity("acct:liz@electricwizard.org", newJwk())
        self.jus = Identity("acct:jus@electricwizard.com", newJwk())
        self.tas = Identity("acct:tas@electricwizard.com", newJwk())
        chainstore().clear()
        for ident in [self.liz, self.jus, self.tas]:
            idchain = IdentityChain(ident, ident.acct)
            chainstore().add(idchain)

    def test_Block(self):
        ident = self.liz

        block = Block(ident, None)
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_list_equal(block._grants, list())
        assert_list_equal(block.payload["grants"], list())

        block = Block(ident, "XXX")
        assert_equals(block.creator, ident.acct)
        assert_equals(block.antecedent, "XXX")
        assert_list_equal(block._grants, list())
        assert_list_equal(block.payload["grants"], list())

    def test_BlockGrants(self):
        ident = self.liz
        block = Block(ident, "XXX")
        grants = []
        for gstr, gtype in Grant.Type.__members__.items():
            g1 = Grant(gstr, "member", "Liz", "tprint1")
            g2 = Grant(gtype, "participant", "Jus", "tprint2")
            grants.append(g1)
            grants.append(g2)
            block.addGrant(g1)
            block.addGrant(g2)

        for bg, g in zip(block.grants, grants):
            assert_dict_equal(bg.toJson(), g.toJson())

    def test_GodBlock(self):
        ident = self.liz

        block = GenesisBlock(ident, "resourceURL")
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_equals(block.resource_uri, "resourceURL")
        assert_equals(block.payload["sub"], "resourceURL")
        assert_equals(block.payload["tid"], authchain.CHAIN_TYPEID)

        block = GenesisBlock(ident, "resourceURL", song="Hide and Seek")
        assert_equals(block.creator, ident.acct)
        assert_is_none(block.antecedent)
        assert_equals(block.resource_uri, "resourceURL")
        assert_equals(block.payload["sub"], "resourceURL")
        assert_equals(block.payload["song"], "Hide and Seek")
        assert_equals(block.payload["tid"], authchain.CHAIN_TYPEID)

        assert_true(block._validateGrants(None))

    def test_chainFactory(self):
        ident = self.jus

        bchain = BlockChain(ident)
        bchain.addBlock(ident)
        bchain.addBlock(ident)
        bchain.addBlock(ident)

        achain = AuthChain(ident, "RESOURCE")

        somechain = BlockChain.deserialize(bchain.serialize(),
                                           factory=chainFactory)
        someotherchain = BlockChain.deserialize(achain.serialize(),
                                                factory=chainFactory)
        assert_is_instance(somechain, BlockChain)
        assert_not_is_instance(somechain, AuthChain)
        assert_is_instance(someotherchain, AuthChain)

    def test_InvalidGrants1(self):
        jus, liz = self.jus, self.liz
        chain = AuthChain(jus, "RESOURCE")

        # There are no grants
        assert_raises(ChainValidationError, chain.validate, chain[0].hash)

        chain[0].addGrant(Grant(Grant.Type.GRANT, "participant",
                                liz.acct, liz.thumbprint))

        # There are no creator grants
        assert_raises(ChainValidationError, chain.validate, chain[0].hash)

        chain[0].addGrant(Grant(Grant.Type.GRANT, "moderator",
                                jus.acct, jus.thumbprint))
        chain.validate(chain[0].hash)

        block1 = chain.addBlock(liz)
        block1.addGrant(Grant(Grant.Type.GRANT, "participant",
                              jus.acct, jus.thumbprint))

        # Liz grant a priv she does not have.
        assert_raises(ChainValidationError, chain.validate, chain[0].hash)

    def testEmptyGrantCheck(self):
        chain = AuthChain(self.tas, "RESOURCE")
        chain._blocks.pop()
        assert_equals(len(chain._blocks), 0)
        assert_is_none(chain.getGrantIdentity(self.tas.acct))

    def testHackedKid(self):
        id_chain = chainstore()[self.tas.acct]
        key1 = self.tas.key
        key2 = self.tas.rotateKey()
        id_chain.addBlock(self.tas, pkt=thumbprint(key2))
        key3 = self.tas.rotateKey()
        id_chain.addBlock(self.tas, pkt=thumbprint(key3))

        chain = AuthChain(self.tas, "RESOURCE")

        chain[0].addGrant(Grant(Grant.Type.VIRAL_GRANT, "participant",
                                self.tas.acct, self.tas.thumbprint))
        chain.addBlock(self.tas).addGrant(Grant(Grant.Type.GRANT,
                                                "participant",
                                                self.jus.acct,
                                                self.jus.thumbprint))
        chain.addBlock(self.tas).addGrant(Grant(Grant.Type.GRANT,
                                                "participant",
                                                self.liz.acct,
                                                self.liz.thumbprint))
        chain.addBlock(self.tas).addGrant(Grant(Grant.Type.REVOKE,
                                                "participant",
                                                self.jus.acct,
                                                self.jus.thumbprint))
        chain.validate(chain[0].hash)
        # Using an old key
        self.tas.rotateKey(key1)
        chain.addBlock(self.tas).addGrant(Grant(Grant.Type.GRANT,
                                                "participant",
                                                self.liz.acct,
                                                self.liz.thumbprint))
        assert_raises(ChainValidationError, chain.validate, chain[0].hash)


def test_DistributedAppExample():
    alice = Identity("acct:alice@example.com", newJwk())
    bob = Identity("acct:bob@example.com", newJwk())
    jack = Identity("acct:jack@example.com", newJwk())
    diane = Identity("acct:diane@example.com", newJwk())
    steve = Identity("acct:steve@example.com", newJwk())

    identities = [alice, bob, jack, diane, steve]

    for id in identities:
        idchain = IdentityChain(id, id.acct)
        chainstore().add(idchain)

    # alice creates an authchain for some resource
    resource = "xmpp:teamroom@conference.example.com"
    alice_chain = AuthChain(alice, resource)

    # alice adds primordial grants and identities to the genesis block
    alice_chain[0].addGrant(Grant(Grant.Type.VIRAL_GRANT, "participant",
                                  alice.acct, alice.thumbprint))
    alice_chain[0].addGrant(Grant(Grant.Type.VIRAL_GRANT, "participant",
                                  bob.acct, bob.thumbprint))
    alice_chain[0].addGrant(Grant(Grant.Type.VIRAL_GRANT, "moderator",
                                  bob.acct, bob.thumbprint))

    # alice serializes the chain and shares it
    alice_chain_blob = alice_chain.serialize()

    # alice shares the hash of the authchain genesis block securely with others
    # (out of scope for now)
    # alice shares the authchain publicly, or sends it directly to others
    # (out of scope for now)

    # bob deserializes alice's authchain
    bob_chain = AuthChain.deserialize(alice_chain_blob)

    assert_equals(alice_chain_blob, bob_chain.serialize())

    # bob adds a new block with grants and identities
    block1 = bob_chain.addBlock(bob)
    block1.addGrant(Grant(Grant.Type.GRANT, "participant", jack.acct,
                          jack.thumbprint))
    block1.addGrant(Grant(Grant.Type.VIRAL_GRANT, "participant", diane.acct,
                          diane.thumbprint))
    block1.addGrant(Grant(Grant.Type.VIRAL_GRANT, "moderator",
                          diane.acct, diane.thumbprint))

    # bob serializes the chain and shares it
    bob_chain_blob = bob_chain.serialize()

    # diane deserializes bob's authchain
    diane_chain = AuthChain.deserialize(bob_chain_blob)

    assert_equals(bob_chain_blob, diane_chain.serialize())

    # diane has viral grant for "participant" privilege, so she can revoke from
    # jack, and grant to steve
    block2 = diane_chain.addBlock(diane)
    block2.addGrant(Grant(Grant.Type.REVOKE, "participant", jack.acct,
                          jack.thumbprint))
    block2.addGrant(Grant(Grant.Type.GRANT, "participant", steve.acct,
                          steve.thumbprint))

    # diane serializes the chain and shares it
    diane_chain_blob = diane_chain.serialize()

    # deserialize diane's authchain
    final_chain = AuthChain.deserialize(diane_chain_blob)

    # print and validate the final chain
    #print("Actual Serialized AuthChain:\n\n" + final_chain.serialize())
    #print("Pretty Printed AuthChain:\n\n" + str(final_chain))

    final_chain.validate(alice_chain.genesis_block.hash)

    # print the policy represented by the authchain
    for acct in [i.acct for i in identities]:
        for priv in ("participant", "moderator"):
            print("{acct} \thas \"{priv}\" privilege: {has}"
                    .format(has=bool(final_chain.hasPrivilege(acct, priv)),
                            **locals()))

    assert_true(final_chain.hasPrivilege(alice.acct, "participant"))
    assert_false(final_chain.hasPrivilege(alice.acct, "moderator"))

    assert_true(final_chain.hasPrivilege(bob.acct, "participant"))
    assert_true(final_chain.hasPrivilege(bob.acct, "moderator"))

    assert_false(final_chain.hasPrivilege(jack.acct, "participant"))
    assert_false(final_chain.hasPrivilege(jack.acct, "moderator"))

    assert_true(final_chain.hasPrivilege(diane.acct, "participant"))
    assert_true(final_chain.hasPrivilege(diane.acct, "moderator"))

    assert_true(final_chain.hasPrivilege(steve.acct, "participant"))
    assert_false(final_chain.hasPrivilege(steve.acct, "moderator"))

    for ident in identities:
        gident = final_chain.getGrantIdentity(ident.acct)
        assert_equal(ident.acct, gident.acct)
        assert_dict_equal(json.loads(ident.key.export()),
                          json.loads(gident.key.export()))
