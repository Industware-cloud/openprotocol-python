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

    def __init__(self, revision: int) -> None:
        self.REVISION = revision

    def __init_subclass__(cls, **kwargs):
        """Auto-register every subclass that defines MID"""
        super().__init_subclass__(**kwargs)
        if cls is OpenProtocolMessage:
            return

        if cls.MESSAGE_TYPE is None:
            raise NotImplementedError(f"{cls.__name__}: MESSAGE_TYPE must be defined")

        parent_set = set()
        for base in cls.__bases__:
            if hasattr(base, "expected_response_mids"):
                parent_set |= base.expected_response_mids
        # If subclass defined its own extra, merge it
        extra_set = getattr(cls, "expected_response_mids", set())
        cls.expected_response_mids = parent_set | extra_set

    @classmethod
    def register(cls: Type["OpenProtocolMessage"]) -> None:
        if cls.MID is None:
            raise ValueError(f"{cls.__name__}: cannot register without MID")
        MidCodec.register(cls.MID, cls)

    def create_message(
        self, revision: int, payload: str = ""
    ) -> OpenProtocolRawMessage:
        if self.MID is None:
            raise NotImplementedError("MID is not defined")
        msg = OpenProtocolRawMessage(self.MID, revision, payload)
        msg.encode()
        return msg

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

    _registry: dict[int, Type[OpenProtocolMessage]] = {}

    @classmethod
    def register(cls, mid: int, parser_cls: Type[OpenProtocolMessage]):
        cls._registry[mid] = parser_cls

    @classmethod
    def decode(cls, raw: bytes) -> OpenProtocolMessage:
        msg = OpenProtocolRawMessage.decode(raw)
        try:
            if msg.mid in cls._registry:
                return cls._registry[msg.mid].from_message(msg)
        except NotImplementedError:
            pass
        raise ValueError(f"Not supported mid {msg.mid}")

    @classmethod
    def encode(cls, mid_obj: OpenProtocolMessage) -> bytes:
        msg = mid_obj.encode()
        return msg.encode()

    @classmethod
    def get_ack(cls, msg: OpenProtocolMessage) -> OpenProtocolMessage | None:
        return None


def register_messages(*message_classes: type[OpenProtocolMessage]) -> None:
    for cls in message_classes:
        cls.register()
