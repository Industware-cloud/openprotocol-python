import pytest
from unittest.mock import AsyncMock

from openprotocol.applications.client import OpenProtocolClient
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage, MidCodec


class DummyMessageRecv(OpenProtocolMessage):
    MID = 9999
    REVISION = 1

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

    def __init__(self, payload="hello"):
        self.payload = payload
        self.expected_response_mid.add(DummyMessageRecv.MID)

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
    dummy_send = DummyMessageSend("hello")
    dummy_send.expected_response_mid.clear()
    dummy_send.expected_response_mid.add(1234)
    #
    with pytest.raises(ValueError):
        await client.send_receive(dummy_send)

    mock_transport.send_receive.assert_called_once()
