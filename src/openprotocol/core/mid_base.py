from abc import abstractmethod, ABC
from enum import Enum, verify, UNIQUE, auto
from typing import Type, ClassVar

from openprotocol.core.message import OpenProtocolRawMessage


@verify(UNIQUE)
class MessageType(Enum):
    REQ_MESSAGE = auto()
    REQ_REPLY_MESSAGE = auto()
    EVENT_SUBSCRIBE = auto()
    EVENT_UNSUBSCRIBE = auto()
    EVENT = auto()
    EVENT_ACK = auto()
    OP_COMMAND = auto()


class OpenProtocolMessage(ABC):
    """Abstract base class for all Open Protocol MID implementations."""

    MID: int | None = None
    REVISION: int | None = None
    expected_response_mids: ClassVar[frozenset[int]] = frozenset()
    MESSAGE_TYPE: MessageType | None = None

    def __init_subclass__(cls, **kwargs):
        """Auto-register every subclass that defines MID/REVISION."""
        super().__init_subclass__(**kwargs)
        if cls.MESSAGE_TYPE is None:
            raise NotImplementedError("MESSAGE_TYPE is not defined")

        if cls.MID is not None and cls.REVISION is not None:
            MidCodec.register(cls.MID, cls.REVISION, cls)

        parent_set = set()
        for base in cls.__bases__:
            if hasattr(base, "expected_response_mids"):
                parent_set |= base.expected_response_mids
        # If subclass defined its own extra, merge it
        extra_set = getattr(cls, "expected_response_mids", set())
        cls.expected_response_mids = parent_set | extra_set

    def create_message(self, payload: str = "") -> OpenProtocolRawMessage:
        if self.MID is None or self.REVISION is None:
            raise NotImplementedError("MID or REVISION is not defined")
        return OpenProtocolRawMessage(self.MID, self.REVISION, payload)

    @abstractmethod
    def encode(self) -> OpenProtocolRawMessage:
        """Encode the MID into an OpenProtocolMessage."""
        pass

    @classmethod
    @abstractmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        """Create a MID instance from an OpenProtocolMessage."""
        pass


class MidCodec:
    LENGTH_FIELD_SIZE = 4  # first 4 chars = frame length

    _registry: dict[tuple[int, int], Type[OpenProtocolMessage]] = {}

    @classmethod
    def register(cls, mid: int, rev: int, parser_cls: Type[OpenProtocolMessage]):
        cls._registry[(mid, rev)] = parser_cls

    @classmethod
    def decode(cls, raw: bytes) -> OpenProtocolMessage:
        msg = OpenProtocolRawMessage.decode(raw)
        key = (msg.mid, msg.revision)
        if key in cls._registry:
            return cls._registry[key].from_message(msg)
        raise ValueError(f"Not supported mid {msg.mid}")

    @classmethod
    def encode(cls, mid_obj: OpenProtocolMessage) -> bytes:
        msg = mid_obj.encode()
        return msg.encode()

    @classmethod
    def get_ack(cls, msg: OpenProtocolMessage) -> OpenProtocolMessage | None:
        return None
