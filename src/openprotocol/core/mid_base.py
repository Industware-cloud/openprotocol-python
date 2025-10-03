from abc import abstractmethod, ABC
from typing import Type

from openprotocol.core.message import OpenProtocolRawMessage


class OpenProtocolMid(ABC):
    """Abstract base class for all Open Protocol MID implementations."""

    MID: int | None = None
    REVISION: int | None = None
    expected_response_mid: set[int] = set()

    def __init_subclass__(cls, **kwargs):
        """Auto-register every subclass that defines MID/REVISION."""
        super().__init_subclass__(**kwargs)
        if cls.MID is not None and cls.REVISION is not None:
            MidCodec.register(cls.MID, cls.REVISION, cls)

    def create_message(self, payload: str) -> OpenProtocolRawMessage:
        return OpenProtocolRawMessage(self.MID, self.REVISION, payload)

    @abstractmethod
    def encode(self) -> OpenProtocolRawMessage:
        """Encode the MID into an OpenProtocolMessage."""
        pass

    @classmethod
    @abstractmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMid":
        """Create a MID instance from an OpenProtocolMessage."""
        pass


class MidCodec:
    LENGTH_FIELD_SIZE = 4  # first 4 chars = frame length

    _registry: dict[tuple[int, int], Type[OpenProtocolMid]] = {}

    @classmethod
    def register(cls, mid: int, rev: int, parser_cls: Type[OpenProtocolMid]):
        cls._registry[(mid, rev)] = parser_cls

    @classmethod
    def decode(cls, raw: bytes) -> OpenProtocolMid:
        msg = OpenProtocolRawMessage.decode(raw)
        key = (msg.mid, msg.revision)
        if key in cls._registry:
            return cls._registry[key].from_message(msg)
        raise ValueError(f"Not supported mid {msg.mid}")

    @classmethod
    def encode(cls, mid_obj: OpenProtocolMid) -> bytes:
        msg = mid_obj.encode()
        return msg.encode()
