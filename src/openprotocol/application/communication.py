from openprotocol.application.base_messages import (
    OpenProtocolReqMsg,
    OpenProtocolReqReplyMsg,
    CommunicationPositiveAck,
    CommunicationNegativeAck,
)
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage
import logging

logger = logging.getLogger(__name__)


class CommunicationStartAcknowledge(OpenProtocolReqReplyMsg):
    MID = 2

    def __init__(
        self,
        revision: int,
        cell_id: int,
        channel_id: int,
        controller_name: str,
        supplier_code: str,
    ):
        super().__init__(revision)
        self._cell_id = cell_id
        self._channel_id = channel_id
        self._controller_name = controller_name
        self._supplier_code = supplier_code

    def encode(self) -> OpenProtocolRawMessage:
        raise NotImplementedError()

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        if msg[20:22] != "01":
            logger.warning(f"Byte 21-22 is not 01 {msg[20:22]}")

        cell_id = int(msg[22:26])
        if msg[26:28] != "02":
            logger.warning(f"Byte 27-28 is not 02 {msg[26:28]}")
        channel_id = int(msg[28:30])

        if msg[30:32] != "03":
            logger.warning(f"Byte 31-32 is not 03 {msg[30:32]}")
        controller_name = msg[32:57]

        if msg[57:59] != "04":
            logger.warning(f"Byte 58-59 is not 04 {msg[57:59]}")
        supplier_code = msg[59:62]

        return cls(msg.revision, cell_id, channel_id, controller_name, supplier_code)


class CommunicationStopMessage(OpenProtocolReqMsg):
    MID = 3
    REVISION = 1

    expected_response_mids = {CommunicationPositiveAck.MID}

    def __init__(self):
        super().__init__(CommunicationStopMessage.REVISION)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        return cls()


class CommunicationStartMessage(OpenProtocolReqMsg):
    MID = 1
    REVISION = 3

    expected_response_mids = {
        CommunicationStartAcknowledge.MID,
        CommunicationNegativeAck.MID,
    }

    def __init__(self):
        super().__init__(CommunicationStartMessage.REVISION)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        return cls()
