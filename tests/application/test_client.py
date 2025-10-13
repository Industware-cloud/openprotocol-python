import asyncio

import pytest
from unittest.mock import AsyncMock

from openprotocol.application.communication import CommunicationStartAcknowledge
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
async def test_connect_starts_client(monkeypatch):
    # Arrange
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)

    # Replace send_receive with mock (we’re not testing message exchange here)

    # Replace listener loop so it doesn’t block forever
    async def dummy_listener_loop():
        await asyncio.sleep(0)

    monkeypatch.setattr(client, "_listener_loop", dummy_listener_loop)

    async def fake_send(_):
        # Simulate that listener loop sets result a bit later
        await asyncio.sleep(0.01)
        if client._pending_future:
            client._pending_future.set_result(
                CommunicationStartAcknowledge(1, 1, 1, "test", "test1")
            )

    mock_transport.send.side_effect = fake_send

    # Act
    await client.connect()

    # Assert
    mock_transport.connect.assert_awaited_once()

    assert client._running
    assert client._startup_done
    assert isinstance(client._listener_task, asyncio.Task)
    mock_transport.send.assert_called_once()

    # Cleanup
    client._listener_task.cancel()
    try:
        await client._listener_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_send_receive_sets_future_result():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._startup_done = True

    async def fake_send(_):
        # Simulate that listener loop sets result a bit later
        await asyncio.sleep(0.01)
        if client._pending_future:
            client._pending_future.set_result(DummyMessageRecv("world"))

    mock_transport.send.side_effect = fake_send

    result = await client.send_receive(DummyMessageSend())
    assert isinstance(result, DummyMessageRecv)
    assert result.payload == "world"
    mock_transport.send.assert_called_once()


@pytest.mark.asyncio
async def test_listener_loop_dispatches_reply():
    mock_transport = AsyncMock()
    mock_transport.receive = AsyncMock(
        side_effect=[
            MidCodec.encode(DummyMessageRecv("OK")),
            asyncio.CancelledError(),  # to break the loop
        ]
    )

    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._pending_future = asyncio.get_running_loop().create_future()
    client._pending_expected = {DummyMessageRecv.MID}

    task = asyncio.create_task(client._listener_loop())
    await asyncio.sleep(0.1)

    # The listener should set the result
    assert client._pending_future.done()
    assert isinstance(client._pending_future.result(), DummyMessageRecv)

    task.cancel()


@pytest.mark.asyncio
async def test_send_receive_not_expected_mid():
    mock_transport = AsyncMock()
    mock_transport.receive = AsyncMock(
        side_effect=[
            MidCodec.encode(DummyMessageSendRes("OK")),
            asyncio.CancelledError(),  # to break the loop
        ]
    )

    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._pending_future = asyncio.get_running_loop().create_future()
    client._pending_expected = set(DummyMessageSendRes.expected_response_mids)

    task = asyncio.create_task(client._listener_loop())
    await asyncio.sleep(0.1)

    # The listener should set the result
    assert client._pending_future.done()
    with pytest.raises(ValueError):
        await client._pending_future.result()

    task.cancel()
    await asyncio.sleep(0.1)
    assert task.done()
