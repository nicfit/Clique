# -*- coding: utf-8 -*-
from jwcrypto.jws import JWS

from .common import thumbprint, Identity
from .keystore import keystore
from .blockchain import BlockChain
from .blockchain import Block as BaseBlock

CHAIN_TYPEID = "identity_XXX"


class Block(BaseBlock):
    def __init__(self, identity, antecedent, pkt=None, **payload):
        super().__init__(identity, antecedent, **payload)
        self._payload["pkt"] = pkt

    @classmethod
    def deserialize(Cls, data, thumbprint, chain):
        key = keystore()[thumbprint]
        identity = Identity(data["iss"] if "iss" in data else chain.creator,
                            key)
        block = Cls(identity, data["ant"] if "ant" in data else None,
                    **data)
        return block

    @property
    def pkt(self):
        return self._payload["pkt"]  # if "pkt" in self._payload else None

    def toJson(self):
        return BaseBlock.toJson(self, omit=("iss",))

    def _validateSignature(self, cvs):
        if cvs.antecedent is None:
            # Special cased to bootstrap data structures
            cvs.ratchet(self)

        jws = JWS()
        jws.deserialize(self.serialize())
        tprint = jws.jose_header["kid"]
        if (cvs.antecedent.pkt == tprint):
            key = keystore()[tprint]
            jws.verify(key)
        else:
            # XXX: This case is only revavent on the GodBlock
            # TODO: support cases where block isn't signed by preceding key
            # (key recovery, issuer tombstone)
            raise NotImplementedError("TODO")                # pragma: no cover


class GenesisBlock(Block):
    def __init__(self, identity, sub=None, **payload):
        super().__init__(identity, None, **payload)
        self._payload["tid"] = CHAIN_TYPEID
        self._payload["sub"] = sub or "CLIQUE"
        self._payload["pkt"] = thumbprint(identity.key)

    @classmethod
    def deserialize(_, data, thumbprint, chain):
        norm_block = Block.deserialize(data, thumbprint, chain)
        gblock = GenesisBlock(norm_block._identity, **data)
        return gblock

    @property
    def subject(self):
        return self._payload["sub"]

    def toJson(self):
        # not calling direct base, iss is desired.
        return BaseBlock.toJson(self)


class Chain(BlockChain):
    BlockType = Block
    GodBlockType = GenesisBlock

    def __init__(self, identity, subject):
        super().__init__()
        self._pkt_order = {}

        self._identity = identity
        if identity:
            # This call sig maps to GenesisBlock ctor because first block
            self.addBlock(identity, subject)

    @staticmethod
    def fromIdentity(ident, subject):
        idchain = None

        # First block is self-signed, the remaining use the previous block's key
        # This means blocks 0 and 1 are signed with the same key.
        keys = [(k, thumbprint(k)) for k in ident.keys]
        k, pkt = keys[0]
        ident.rotateKey(k)
        idchain = Chain(ident, subject)

        for _, pkt in keys[1:]:
            ident.rotateKey(keystore()[idchain[-1].pkt])
            idchain.addBlock(ident, pkt=pkt)

        return idchain

    def _newBlock(self, block):
        self._pkt_order[block.pkt] = len(self._pkt_order)

    @property
    def subject(self):
        return self.genesis_block.subject

    @property
    def creator(self):
        return self.genesis_block.creator

    # FIXME: this method name
    def isSameOrSubsequent(self, tp1, tp2):
        return self._pkt_order[tp1] >= self._pkt_order[tp2]

    def addBlock(self, identity, *args, **kwargs):
        block = super().addBlock(identity, *args, **kwargs)
        assert(block.pkt)
        self._pkt_order[block.pkt] = len(self._pkt_order)
        return block
