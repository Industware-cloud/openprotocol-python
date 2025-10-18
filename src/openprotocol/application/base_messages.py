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
        super().__init__(revision)
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
        super().__init__(revision)
        self._mid = mid

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        mid = int(msg[20:24])
        return cls(msg.revision, mid)


class OpenProtocolReqMsg(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    # NACK or some data
    expected_response_mids = {
        CommunicationNegativeAck.MID,
    }

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


class OpenProtocolEventSubscribe(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT_SUBSCRIBE
    expected_response_mids = {
        CommunicationNegativeAck.MID,
        CommunicationPositiveAck.MID,
    }
    # Mid of event to be subscribed
    MID_EVENT = None

    def __init__(self, revision: int = 1) -> None:
        """
        :param revision: The revision is used to inform controller which revision to subscribe to
                any class should set the revision based on supported decoding of EventData
        """
        super().__init__(revision)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


class OpenProtocolEventUnsubscribe(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT_UNSUBSCRIBE
    expected_response_mids = {
        CommunicationNegativeAck.MID,
        CommunicationPositiveAck.MID,
    }
    # Mid of event to be unsubscribed
    MID_EVENT = None
    REVISION = 1

    def __init__(self):
        super().__init__(self.REVISION)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


class OpenProtocolEventACK(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT_ACK

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


class OpenProtocolEvent(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.EVENT
    # ack message or nothing depends on the ack flag


class OpenProtocolCommandMsg(OpenProtocolMessage, ABC):
    MESSAGE_TYPE = MessageType.OP_COMMAND
    # Response only ACK or NACK
    expected_response_mids = {
        CommunicationNegativeAck.MID,
        CommunicationPositiveAck.MID,
    }

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()
