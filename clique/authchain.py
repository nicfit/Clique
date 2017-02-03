# -*- coding: utf-8 -*-
from enum import Enum
from collections import OrderedDict

from jwcrypto.jws import JWS

from .keystore import keystore
from .chainstore import chainstore
from .common import Uri, JsonType, Identity
from .blockchain import Block as BaseBlock
from .blockchain import BlockChain, ChainValidationError
from .blockchain import _ChainValidationState as _ChainValidationStateBase

CHAIN_TYPEID = "auth_XXX"


class Grant(JsonType):
    class Type(Enum):
        VIRAL_GRANT = 1
        GRANT = 2
        REVOKE = 3

    def __init__(self, type_, privilege, grantee, tprint):
        if isinstance(type_, str):
            if type_ in Grant.Type.__members__:
                type_ = Grant.Type.__members__[type_]
            else:
                raise ValueError("Invalid Grant.Type: {}".format(type_))
        elif type(type_) is not Grant.Type:
            raise ValueError("Invalid Grant.Type: {}".format(type_))

        self.type = type_
        self.privilege = privilege
        self.grantee = str(Uri.create(grantee))
        self.thumbprint = tprint

    def toJson(self):
        d = OrderedDict()
        d["type"] = self.type.name
        d["privilege"] = self.privilege
        d["grantee"] = self.grantee
        d["thumbprint"] = self.thumbprint
        return d

    @classmethod
    def fromJson(_, data):
        grant = Grant(Grant.Type.__members__[data["type"]],
                      data["privilege"], data["grantee"],
                      data["thumbprint"])
        return grant


class Block(BaseBlock):
    def __init__(self, identity, antecedent, **payload):
        super().__init__(identity, antecedent, **payload)
        self._grants = []
        self._payload["grants"] = []

    @property
    def grants(self):
        for grant in self._grants:
            yield grant

    def addGrant(self, grant):
        self._grants.append(grant)

    def toJson(self):
        self._payload["grants"] = []
        for grant in self._grants:
            self._payload["grants"].append(grant.toJson())

        return super().toJson(omit=("pkt",))

    @classmethod
    def deserialize(Cls, data, thumbprint, chain):
        creator = Identity(data["iss"], keystore()[thumbprint])

        grants = []
        for g in data["grants"]:
            grant = Grant.fromJson(g)
            grants.append(grant)

        block = Cls(creator, data["ant"] if "ant" in data else None, **data)
        for g in grants:
            block.addGrant(g)
        return block

    def validate(self, cvs):
        super().validate(cvs)
        self._validateGrants(cvs)

    def _validateSignature(self, cvs):
        if cvs.antecedent is None:
            # Special cased to bootstrap data structures
            cvs.ratchet(self)

        jws = JWS()
        jws.deserialize(self.serialize())
        tprint = jws.jose_header["kid"]
        idchain = chainstore()[self.creator]
        if self.creator not in cvs._recent_thumbprints:
            raise ChainValidationError("No grants for creator: " + self.creator)
        creator_print = cvs._recent_thumbprints[self.creator]

        if idchain.isSameOrSubsequent(tprint, creator_print):
            key = keystore()[tprint]
            jws.verify(key)
        else:
            raise ChainValidationError("Out of date key.")

    def _validateGrants(self, cvs):
        creator_grants = cvs._current_grants[self.creator]
        assert(creator_grants)

        for grant in self.grants:
            priv = grant.privilege
            if (priv not in creator_grants or
                    creator_grants[priv].type != Grant.Type.VIRAL_GRANT):
                raise ChainValidationError("Failed grant check")


class GenesisBlock(Block):
    def __init__(self, identity, resource_uri, **payload):
        super().__init__(identity, None, **payload)
        self._payload["tid"] = CHAIN_TYPEID
        self._payload["sub"] = str(resource_uri)

    @property
    def resource_uri(self):
        return self._payload["sub"]

    @classmethod
    def deserialize(_, data, thumbprint, chain):
        norm_block = Block.deserialize(data, thumbprint, chain)
        gblock = GenesisBlock(norm_block._identity, data["sub"])
        gblock._grants = norm_block._grants
        return gblock

    def _validateGrants(self, cvs):
        return True


class Chain(BlockChain):
    BlockType = Block
    GodBlockType = GenesisBlock

    def __init__(self, identity, resource_uri):
        super().__init__()
        if identity and resource_uri:
            self.addBlock(identity, resource_uri)

    def hasPrivilege(self, acct, privilege):
        for block in reversed(self):
            for grant in block.grants:
                if grant.grantee == acct and grant.privilege == privilege:
                    return grant.type != Grant.Type.REVOKE
        return False

    def getGrantIdentity(self, acct):
        for block in reversed(self):
            for g in block.grants:
                if g.grantee == acct:
                    key = keystore()[g.thumbprint]
                    return Identity(acct, key)
        return None

    def validate(self, genesis_block_hash):
        class _ChainValidationState(_ChainValidationStateBase):
            def __init__(self, chain):
                super().__init__(chain)

                self._recent_thumbprints = {}
                self._current_grants = {}

            def ratchet(self, block):
                for grant in block.grants:
                    if grant.grantee not in self._current_grants:
                        self._current_grants[grant.grantee] = {}

                    self._current_grants[grant.grantee][grant.privilege] = grant
                    self._recent_thumbprints[grant.grantee] = grant.thumbprint

                super().ratchet(block)

        return super().validate(genesis_block_hash,
                                ChainValidationClass=_ChainValidationState)
