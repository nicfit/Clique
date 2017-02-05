#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from nose.tools import assert_equals, assert_dict_equal

from jwcrypto.jwk import JWK
from clique.authchain import Grant
from clique import Identity, IdentityChain, AuthChain, keystore, chainstore
from clique import useCliqueServer  # noqa


def main():
    #useCliqueServer("https://outer-planes.net/clique")   # noqa

    for id in global_identities:
        keystore().add(id.key)
        keystore().upload(id.key)

    if authchain() and identitychain():
        print("SUCCESS")
    else:
        print("FAILURE")


def identitychain():
    print()
    print("*" * 12 + "IdentityChain" + "*" * 12)

    eddie = Identity("acct:eddie@vanhalen.com", Identity.generateKey())
    keystore().upload(eddie.key)
    first_key = eddie.key
    eddie_chain = IdentityChain(eddie, "guitar:lead")
    print("Subject: " + eddie_chain.subject)
    print("GenesisBlock Pkt: " + eddie_chain.genesis_block.pkt)

    for _ in range(5):
        k = Identity.generateKey()
        eddie_chain.addBlock(eddie, pkt=k.key_id)
        eddie.rotateKey(k)
    serialized = eddie_chain.serialize()
    print("Eddie IdentityChain:\n{}".format(serialized))
    print(eddie_chain)

    copy = IdentityChain.deserialize(serialized)
    serialized2 = copy.serialize()
    print("Copy IdentityChain:\n{}".format(serialized))

    assert(serialized == serialized2)
    assert(eddie_chain.subject == copy.subject)

    copy.validate(eddie_chain.genesis_block.hash)
    print(eddie_chain)

    print("-" * 80)
    eddie.rotateKey(first_key)
    copy2 = IdentityChain.fromIdentity(eddie, "guitar:lead")
    print(copy2)
    print(copy2.serialize())

    # Due to reserialization the hashes and serializations will not be equal,
    # the json must be.
    copy2.validate(copy2.genesis_block.hash)
    assert_equals(len(eddie_chain), len(copy2))
    for oblock, cblock in zip(eddie_chain, copy):
        o = oblock.toJson()
        c = cblock.toJson()
        if "ant" in o:
            del o["ant"]
            del c["ant"]
        assert_dict_equal(o, c)

    return True


def authchain():
    for id in global_identities:
        idchain = IdentityChain(id, id.acct)
        chainstore().add(idchain)

    # alice creates an authchain for some resource
    resource = "xmpp:teamroom@conference.example.com"
    alice_chain = AuthChain(alice, resource)

    # alice adds primordial grants and identities to the genesis block
    alice_chain[0].addGrant(Grant("VIRAL_GRANT", "participant",
                                  alice.acct, alice.thumbprint))
    alice_chain[0].addGrant(Grant("VIRAL_GRANT", "participant",
                                  bob.acct, bob.thumbprint))
    alice_chain[0].addGrant(Grant("VIRAL_GRANT", "moderator",
                                  bob.acct, bob.thumbprint))

    # alice serializes the chain and shares it
    alice_chain_blob = alice_chain.serialize()

    # alice shares the hash of the authchain genesis block securely with others
    # (out of scope for now)
    # alice shares the authchain publicly, or sends it directly to others
    # (out of scope for now)

    # bob deserializes alice's authchain
    bob_chain = AuthChain.deserialize(alice_chain_blob)

    # bob adds a new block with grants and identities
    block1 = bob_chain.addBlock(bob)
    block1.addGrant(Grant("GRANT", "participant", jack.acct,
                          jack.thumbprint))
    block1.addGrant(Grant("VIRAL_GRANT", "participant", diane.acct,
                          diane.thumbprint))
    block1.addGrant(Grant("VIRAL_GRANT", "moderator",
                          diane.acct, diane.thumbprint))

    # bob serializes the chain and shares it
    bob_chain_blob = bob_chain.serialize()

    # diane deserializes bob's authchain
    diane_chain = AuthChain.deserialize(bob_chain_blob)
    # diane has viral grant for "participant" privilege, so she can revoke from
    # jack, and grant to steve
    block2 = diane_chain.addBlock(diane)
    block2.addGrant(Grant("REVOKE", "participant", jack.acct,
                          jack.thumbprint))
    block2.addGrant(Grant("GRANT", "participant", steve.acct,
                          steve.thumbprint))

    # diane serializes the chain and shares it
    diane_chain_blob = diane_chain.serialize()

    # deserialize diane's authchain
    final_chain = AuthChain.deserialize(diane_chain_blob)

    # print and validate the final chain
    print("Actual Serialized AuthChain:\n\n" + final_chain.serialize())
    print("Pretty Printed AuthChain:\n\n" + str(final_chain))

    final_chain.validate(alice_chain.genesis_block.hash)

    # print the policy represented by the authchain
    for acct in [i.acct for i in global_identities]:
        for priv in ("participant", "moderator"):
            print("{acct} \thas \"{priv}\" privilege: {has}"
                    .format(has=bool(final_chain.hasPrivilege(acct, priv)),
                            **locals()))
    return True


alice = Identity("acct:alice@example.com",
                 JWK(**{#"cmt": "alice",  # noqa
                        "crv": "P-256",
                        "d": "z-CuqNSEkOyoXWlGcoqgaq_nh6WlgtcV8ZroeNQ5AS0",
                        "kid": "ZansZqsUXsTucfJC6t3ApBXAsXfR4spy4MmFOHek5Qc",
                        "kty": "EC",
                        "size": 256,
                        "x": "qKKAfUpLUsjFlsRzhyJpUrLZ3vr_Fu4yf6-0bXnsx1w",
                        "y": "xkJVvFpTuTXou0xkXpiVlsldjH10Qj5831ZJbrFHNPQ"
                   }))
bob = Identity("acct:bob@example.com",
               JWK(**{#"cmt": "bob",  # noqa
                      "crv": "P-256",
                      "d": "fgug1klBZUQr83wVDVwLj9odTOwfTQ9wbTw2rMZyhJQ",
                      "kid": "SETKquASXDG0k5ERRAa4kvXNAGGWfkZxvfEOxks9tHU",
                      "kty": "EC",
                      "size": 256,
                      "x": "rlzWtZtPq1fFxutc0BUvP8Nib61s-BWzE65OfgCnYYo",
                      "y": "CCnBEEsnzAMU0YbyFRrDPuHoDHGD6mt54RwWtLH8e3E"
                 }))
jack = Identity("acct:jack@example.com",
                JWK(**{#"cmt": "jack",  # noqa
                       "crv": "P-256",
                       "d": "0FYEyIkPZT3xAKh226266nqUg5e9NWl88-TFn0pLcmY",
                       "kid": "OsY_R82yHLKXxVVZl-f5aBaqpN4yH9wSyeLwxTy_8Lo",
                       "kty": "EC",
                       "size": 256,
                       "x": "4WvWVb-VPWoJct6upf99jiRK8uuFJuHZJdIa0Z1F-x0",
                       "y": "5digz6ao89Kw9p50VRk9P0SbbKwrqwQdBMqoKhjTCu8"
                      }))
diane = Identity("acct:diane@example.com",
                 JWK(**{#"cmt": "diane",  # noqa
                        "crv": "P-256",
                        "d": "xqoqU02XMyVQfTYEwLDt1kNGM9IOqvfrbMk-K-c_thM",
                        "kid": "2PgeWCJIN2Btmp_FcfIqephBFAYmJ8Gp0v1XZ0Gm-c8",
                        "kty": "EC",
                        "size": 256,
                        "x": "umuIMUX3dqgUP67HfiJGTVzLBOB1-KjQnpG9cZ8q9sI",
                        "y": "2i4A23HuPwY7yu_p9-sb3xM9uGQkBD7jxOJ20Vx1mzY"
                       }))
steve = Identity("acct:steve@example.com",
                 JWK(**{#"cmt": "steve",  # noqa
                        "crv": "P-256",
                        "d": "5yOV5PUmopGZUEZ1QJcnwvb8dMQaBv275h87QaK1U3o",
                        "kid": "NP7aCbQTrZEKFfnNYxU1mPgDdYLokQt13cpFAEE7zAk",
                        "kty": "EC",
                        "size": 256,
                        "x": "J9wofOniY5bP1m1ppF1LiHYl7YuSd8sKbKeh2phdBT8",
                        "y": "ikK1rfGon8gnYueUDUzHGRMkF3NV4oSxrpMJIz9ZsQU"
                       }))

global_identities = [alice, bob, jack, diane, steve]


if __name__ == "__main__":
    sys.exit(main() or 0)
