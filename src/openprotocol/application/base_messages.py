from abc import ABC

from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage, MessageType


class OpenProtocolReqReplyMsg(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.REQ_REPLY_MESSAGE
    # no answer

    def encode(self) -> OpenProtocolRawMessage:
        raise NotImplementedError()


class CommunicationNegativeAck(OpenProtocolReqReplyMsg):
    MID = 4

    def __init__(self, revision, mid, err_code):
        self._revision = revision
        self._mid = mid
        self._err_code = err_code

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        mid = int(msg[20:24])
        if msg.revision == 1:
            err_code = int(msg[24:26])
        else:
            err_code = int(msg[24:27])
        return cls(msg.revision, mid, err_code)


class CommunicationPositiveAck(OpenProtocolReqReplyMsg):
    MID = 5

    def __init__(self, revision, mid):
        self._revision = revision
        self._mid = mid

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        mid = int(msg[20:24])
        return cls(msg.revision, mid)


class OpenProtocolReqMsg(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = {CommunicationNegativeAck.MID}

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


class OpenProtocolEventSubscribe(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT_SUBSCRIBE
    expected_response_mids = {
        CommunicationNegativeAck.MID,
        CommunicationPositiveAck.MID,
    }


class OpenProtocolEventACK(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT_ACK


class OpenProtocolEvent(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT
    # ack message or nothing depends on the ack flag


class OpenProtocolCommandMsg(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.OP_COMMAND
    expected_response_mids = {
        CommunicationNegativeAck.MID,
        CommunicationPositiveAck.MID,
    }
