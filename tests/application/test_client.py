import pytest
from unittest.mock import AsyncMock

from openprotocol.application.client import OpenProtocolClient
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage, MidCodec, MessageType


class DummyMessageRecv(OpenProtocolMessage):
    MID = 9999
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_REPLY_MESSAGE

    def __init__(self, payload="hello"):
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.payload)


class DummyMessageSend(OpenProtocolMessage):
    MID = 9998
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = frozenset({DummyMessageRecv.MID})

    def __init__(self, payload="hello"):
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.payload)


class DummyMessageSendRes(OpenProtocolMessage):
    MID = 9998
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = frozenset({1234})

    def __init__(self, payload="hello"):
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.payload)


@pytest.mark.asyncio
async def test_send_receive():
    # Mock transport
    mock_transport = AsyncMock()
    mock_transport.send_receive.return_value = MidCodec.encode(
        DummyMessageRecv("world")
    )

    # System under test
    client = OpenProtocolClient(mock_transport)

    # Act
    response = await client.send_receive(DummyMessageSend("hello"))

    # Assert
    assert isinstance(response, DummyMessageRecv)
    assert response.payload == "world"
    mock_transport.send_receive.assert_called_once()


@pytest.mark.asyncio
async def test_send_receive_not_expected_mid():
    mock_transport = AsyncMock()
    mock_transport.send_receive.return_value = MidCodec.encode(
        DummyMessageRecv("world")
    )

    client = OpenProtocolClient(mock_transport)
    dummy_send = DummyMessageSendRes("hello")
    #
    with pytest.raises(ValueError):
        await client.send_receive(dummy_send)

    mock_transport.send_receive.assert_called_once()


@pytest.mark.asyncio
async def test_send_receive_inherit_mids():
    # Mock transport
    mock_transport = AsyncMock()
    mock_transport.send_receive.return_value = MidCodec.encode(
        DummyMessageRecv("world")
    )

    class DummyMessageSendInherit(DummyMessageSend):
        MID = 9998
        REVISION = 1
        MESSAGE_TYPE = MessageType.REQ_MESSAGE
        expected_response_mids = {1234}

    # System under test
    client = OpenProtocolClient(mock_transport)

    # Act
    response = await client.send_receive(DummyMessageSendInherit("hello"))

    # Assert
    assert isinstance(response, DummyMessageRecv)
    assert response.payload == "world"
    mock_transport.send_receive.assert_called_once()
