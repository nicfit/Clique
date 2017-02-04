# -*- coding: utf-8 -*-
import json
from hashlib import sha256
from collections import OrderedDict

from jwcrypto.jwt import JWT

from .keystore import keystore
from .common import JsonType, Identity, thumbprint

from . import getLogger
log = getLogger(__name__)


class Block(JsonType):
    def __init__(self, identity, antecedent, **payload):
        self._identity = identity
        # Set the active key, it could change before the block is signed.
        self._key = identity.key

        self._serialization = None

        self._payload = OrderedDict()
        self._payload["iss"] = self.creator
        if antecedent:
            self.antecedent = antecedent
        self._updatePayload(payload)

    def _updatePayload(self, d):
        """Merge dict ``d`` into ``self._payload`` if without they values are
        not in payload."""
        d = d or {}
        self._payload.update({k: v for k, v in d.items()
                                   if k not in self._payload})

    @classmethod
    def deserialize(Cls, data, thumbprint, chain):
        key = keystore()[thumbprint]
        identity = Identity(data["iss"], key)
        block = Cls(identity, data["ant"] if "ant" in data else None,
                    **data)
        return block

    @property
    def creator(self):
        return self._identity.acct

    @property
    def payload(self):
        return self._payload

    @property
    def antecedent(self):
        return self._payload["ant"] if "ant" in self._payload else None

    @antecedent.setter
    def antecedent(self, ant):
        if ant:
            self._payload["ant"] = ant
        elif "ant" in self._payload:
            del self._payload["ant"]

    def toJson(self, omit=None, remap=None, add=None):
        if self.antecedent:
            self._payload["ant"] = self.antecedent

        d = dict(self._payload)
        for o in (omit or []):
            if o in d:
                del d[o]
        for old, new in (remap or {}).items():
            d[new] = d[old]
            del d[old]
        for k, v in (add or {}).items():
            if k in d:
                raise ValueError("value exists: {}={}".format(k, v))
            d[k] = v
        return d

    @classmethod
    def _fromSerialization(BlockClass, serialized, chain):
        jwt = JWT()
        jwt.deserialize(serialized)

        jws = jwt.token
        block_json = json.loads(str(jws.objects["payload"], "utf8"))
        block = BlockClass.deserialize(block_json, jws.jose_header["kid"],
                                       chain)
        block._serialization = serialized

        return block

    def _serialize(self):
        """Performs the serialization but the object is not "frozen" by setting
        ``_serialization``.
        """
        h = {"alg": "ES256",
             "kid": thumbprint(self._key),
            }
        jwt = JWT(header=h, claims=self.toJson())
        jwt.make_signed_token(self._key)
        log.debug("Block signed with key thumbprint: {}".format(h["kid"]))
        return jwt.serialize()

    def serialize(self, update=False):
        if self._serialization is None or update:
            self._serialization = self._serialize()
        return self._serialization

    @property
    def hash(self):
        # FIXME: can't pass update arg since @property
        s = self.serialize(update=False)
        hfunc = sha256()
        hfunc.update(s.encode("utf8"))
        return hfunc.hexdigest()

    def validate(self, cvs):
        self._validateAntecedent(cvs)
        self._validateSignature(cvs)
        return True

    def _validateAntecedent(self, cvs):
        antecedent_hash = cvs.antecedent.hash if cvs.antecedent else None
        if self.antecedent != antecedent_hash:
            raise ChainValidationError(
                    "Antecedent hash mismatch: {} (self) != {} (antecedent)"
                    .format(self.antecedent, antecedent_hash))

    def _validateSignature(self, cvs):
        if cvs.antecedent is None:
            # Special cased to bootstrap data structures
            cvs.ratchet(self)
        self.verify()

    def verify(self, key=None):
        jwt = JWT()
        jwt.deserialize(self.serialize())
        jws = jwt.token

        if not key:
            tprint = jws.jose_header["kid"]
            key = keystore()[tprint]
        jws.verify(key)

    def __str__(self):
        return json.dumps(self.toJson(), indent=2, sort_keys=True)


class BlockChain(JsonType):
    BlockType = Block
    GodBlockType = Block

    """A base class for all types of block chains."""
    def __init__(self, *_):
        self._blocks = []

    def _newBlock(self, block):
        """Invoked before ``block`` is added to the chain."""
        pass

    def _appendBlock(self, block):
        self._newBlock(block)
        self._blocks.append(block)

    def addBlock(self, identity, *args, **kwargs):
        antecedent = self._blocks[-1] if self._blocks else None
        if antecedent:
            block = self.BlockType(identity, antecedent.hash, *args, **kwargs)
        else:
            if self.GodBlockType is self.BlockType:
                # antecedent hash arg required base Block types
                args = (None, ) + args
            block = self.GodBlockType(identity, *args, **kwargs)
        self._appendBlock(block)
        return block

    def toJson(self):
        return [b.toJson() for b in self._blocks]

    @property
    def genesis_block(self):
        """Returns the first block in the chain.

        Raises:
            IndexError: If there are no blocks in the chain.
        """
        return self._blocks[0]
    god_block = genesis_block

    def __getitem__(self, i):
        return self._blocks[i]

    def __len__(self):
        return len(self._blocks)

    def __iter__(self):
        return iter(self._blocks)

    def __reversed__(self):
        return reversed(self._blocks)

    def __iadd__(self, rhs):
        if len(self._blocks) == 0:
            rhs.antecedent = None
        else:
            rhs.antecedent = self._blocks[-1].hash
        self._appendBlock(rhs)
        return self

    def serialize(self, update=False):
        """Returns the serialized BlockChain as a JSON string."""
        return json.dumps([b.serialize(update=False) for b in self._blocks])

    @classmethod
    def deserialize(ChainClass, serialization, factory=None):
        chain = ChainClass(None, None)
        chain_json = json.loads(serialization)

        if len(chain_json) == 0:
            return chain

        block = ChainClass.GodBlockType._fromSerialization(chain_json[0], chain)

        if factory:
            factory_chain = factory(block, serialization)
            if factory_chain:
                return factory_chain

        chain._appendBlock(block)
        for serialized in chain_json[1:]:
            block = ChainClass.BlockType._fromSerialization(serialized, chain)
            chain._appendBlock(block)

        return chain

    def validate(self, genesis_block_hash, ChainValidationClass=None):
        ChainValidationClass = ChainValidationClass or _ChainValidationState
        if self[0].hash != genesis_block_hash:
            raise ChainValidationError(
                    "Genesis hash mismatch: {} (self) != {} (requested)"
                    .format(self.genesis_block.hash, genesis_block_hash))

        cvs = ChainValidationClass(self)
        for block in self:
            block.validate(cvs)
            cvs.ratchet(block)

    def __str__(self):
        chain_str = ""
        for i, block in enumerate(self, 0):
            block_str = str(block)
            chain_str += "Block #{i:d}:\n{block_str}\n".format(**locals())
        return chain_str


class ChainValidationError(Exception):
    def __bool__(self):
        return False


class _ChainValidationState(object):
    def __init__(self, chain):
        self.chain = chain
        self.antecedent = None

    def ratchet(self, block):
        self.antecedent = block
