import asyncio

import pytest
from unittest.mock import AsyncMock

from openprotocol.application.base_messages import (
    OpenProtocolEventSubscribe,
    CommunicationPositiveAck,
    CommunicationNegativeAck,
    OpenProtocolEventUnsubscribe,
)
from openprotocol.application.communication import CommunicationStartAcknowledge
from openprotocol.application.client import OpenProtocolClient
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage, MidCodec, MessageType


class DummyMessageRecv(OpenProtocolMessage):
    MID = 9999
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_REPLY_MESSAGE

    def __init__(self, payload="hello"):
        super().__init__(self.REVISION)
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION, self.payload)


class DummyMessageNoResp(OpenProtocolMessage):
    MID = 9997
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = frozenset([])

    def __init__(self, payload="hello"):
        super().__init__(self.REVISION)
        self.payload = payload

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION, self.payload)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)


class DummyMessageSend(OpenProtocolMessage):
    MID = 9998
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = frozenset({DummyMessageRecv.MID})

    def __init__(self, payload="hello"):
        super().__init__(self.REVISION)
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION, self.payload)


class DummyMessageSendRes(OpenProtocolMessage):
    MID = 9998
    REVISION = 1
    MESSAGE_TYPE = MessageType.REQ_MESSAGE
    expected_response_mids = frozenset({1234})

    def __init__(self, payload="hello"):
        super().__init__(self.REVISION)
        self.payload = payload

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage):
        return cls(msg.payload)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION, self.payload)


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
async def test_send_receive_no_response():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._startup_done = True

    with pytest.raises(ValueError):
        await client.send_receive(DummyMessageNoResp())
    mock_transport.send.assert_not_called()


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


class DummySubscribeMidNoEvent(OpenProtocolEventSubscribe):
    MID = 42
    REVISION = 1

    def encode(self):
        return b"dummy"

    @classmethod
    def from_message(cls, msg):
        return cls(msg.revision)


class DummySubscribeMid(OpenProtocolEventSubscribe):
    MID = 42
    REVISION = 1
    MID_EVENT = 10

    def encode(self):
        return b"dummy"

    @classmethod
    def from_message(cls, msg):
        return cls()


class DummyUnsubscribeMidNoEvent(OpenProtocolEventUnsubscribe):
    MID = 44
    REVISION = 1

    def encode(self):
        return b"dummy"

    @classmethod
    def from_message(cls, msg):
        return cls()


class DummyUnsubscribeMid(OpenProtocolEventUnsubscribe):
    MID = 44
    REVISION = 1
    MID_EVENT = 10

    def encode(self):
        return b"dummy"

    @classmethod
    def from_message(cls, msg):
        return cls()


@pytest.mark.asyncio
async def test_subscribe_incorrect_mid():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)

    with pytest.raises(RuntimeError):
        await client.subscribe(DummySubscribeMidNoEvent)


@pytest.mark.asyncio
async def test_unsubscribe_incorrect_mid():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)

    with pytest.raises(RuntimeError):
        await client.unsubscribe(DummyUnsubscribeMidNoEvent)


@pytest.mark.asyncio
async def test_subscribe_waits_for_ack_and_registers():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._startup_done = True
    client._running = True

    # Mock send_receive to return ACK
    client.send_receive = AsyncMock(
        return_value=CommunicationPositiveAck(
            DummySubscribeMid.REVISION, DummySubscribeMid.MID
        )
    )

    await client.subscribe(DummySubscribeMid)

    # Now it should be registered
    assert DummySubscribeMid.MID_EVENT in client._subscribed_mids
    client.send_receive.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_raises_on_nack():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._startup_done = True
    client._running = True

    client.send_receive = AsyncMock(
        return_value=CommunicationNegativeAck(
            DummySubscribeMid.REVISION, DummySubscribeMid.MID, 1
        )
    )

    with pytest.raises(RuntimeError):
        await client.subscribe(DummySubscribeMid)

    # Should NOT register
    assert DummySubscribeMid.MID not in client._subscribed_mids


@pytest.mark.asyncio
async def test_get_subscription_waits_then_receives():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._startup_done = True
    client._running = True
    msg = DummyMessageSend()

    async def delayed_put():
        await asyncio.sleep(0.1)
        await client._subscription_queue.put(msg)

    asyncio.create_task(delayed_put())

    result = await client.get_subscription()
    assert result is msg


@pytest.mark.asyncio
async def test_unsubscribe_success_registers_removed():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    # prepare client as if already connected/subscribed
    client._running = True
    client._startup_done = True
    client._subscribed_mids.add(DummyUnsubscribeMid.MID)

    # Mock send_receive to return ACK
    client.send_receive = AsyncMock(
        return_value=CommunicationPositiveAck(
            DummyUnsubscribeMid.REVISION, DummyUnsubscribeMid.MID
        )
    )

    # Act
    await client.unsubscribe(DummyUnsubscribeMid)

    # Assert: unsubscribed removed and send_receive called
    assert DummyUnsubscribeMid.MID_EVENT not in client._subscribed_mids
    client.send_receive.assert_awaited_once()


@pytest.mark.asyncio
async def test_unsubscribe_rejected_raises_and_keeps_subscription():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._startup_done = True
    client._subscribed_mids.add(DummyUnsubscribeMid.MID_EVENT)

    # Mock send_receive to return NACK
    client.send_receive = AsyncMock(
        return_value=CommunicationNegativeAck(
            DummyUnsubscribeMid.REVISION, DummyUnsubscribeMid.MID, 1
        )
    )

    # Act / Assert
    with pytest.raises(RuntimeError):
        await client.unsubscribe(DummyUnsubscribeMid)

    # Ensure subscription still present
    assert DummyUnsubscribeMid.MID_EVENT in client._subscribed_mids
    client.send_receive.assert_awaited_once()


@pytest.mark.asyncio
async def test_unsubscribe_rejected_raises_and_keeps_subscription_force():
    mock_transport = AsyncMock()
    client = OpenProtocolClient(mock_transport)
    client._running = True
    client._startup_done = True
    client._subscribed_mids.add(DummyUnsubscribeMid.MID_EVENT)

    # Mock send_receive to return NACK
    client.send_receive = AsyncMock(
        return_value=CommunicationNegativeAck(
            DummyUnsubscribeMid.REVISION, DummyUnsubscribeMid.MID, 1
        )
    )

    await client.unsubscribe(DummyUnsubscribeMid, force=True)

    # Ensure subscription still present
    assert DummyUnsubscribeMid.MID_EVENT not in client._subscribed_mids
    client.send_receive.assert_awaited_once()
