import asyncio
import logging
from asyncio import CancelledError
from typing import Optional, Type, Set

from openprotocol.application.communication import (
    CommunicationStartMessage,
    CommunicationStopMessage,
    CommunicationStartAcknowledge,
)
from openprotocol.transport import AsyncTcpClient
from openprotocol.core.mid_base import MidCodec, MessageType, OpenProtocolMessage

logger = logging.getLogger(__name__)


class OpenProtocolClient:
    def __init__(self, transport: AsyncTcpClient, keepalive_interval: float = 15.0):
        self._transport: AsyncTcpClient = transport
        self._keepalive_interval: float = keepalive_interval
        self._startup_done: bool = False
        self._running: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

        # Background tasks
        self._keepalive_task: Optional[asyncio.Task] = None
        self._listener_task: Optional[asyncio.Task] = None

        # Pending request-response
        self._pending_future: Optional[asyncio.Future] = None
        self._pending_expected: Set[int] = set()

    @classmethod
    def create(
        cls, host: str, port: int, keepalive_interval: float = 15.0
    ) -> "OpenProtocolClient":
        transport = AsyncTcpClient(host, port)
        return cls(transport, keepalive_interval)

    async def connect(self) -> None:
        """Connect to server, run startup sequence, and start background loops."""
        await self._transport.connect()
        self._running = True
        comm_start_mid = CommunicationStartMessage()
        comm = await self.send_receive(comm_start_mid)
        if not isinstance(comm, CommunicationStartAcknowledge):
            raise ConnectionError(f"Communication not acknowledged")
        self._startup_done = True

        self._listener_task = asyncio.create_task(self._listener_loop())

    async def _close(self) -> None:
        """Stop background tasks and close transport."""
        self._running = False
        self._startup_done = False

        for task in (self._listener_task, self._keepalive_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await self._transport.close()

    async def disconnect(self) -> None:
        """Disconnect from server."""
        if not self._running or not self._startup_done:
            return

        await self.send_receive(CommunicationStopMessage())
        await self._close()

    async def send_receive(
        self, mid_obj: OpenProtocolMessage, timeout: float = 5.0
    ) -> OpenProtocolMessage | None:
        """Send a MID and wait for its reply (if applicable)."""
        if not self._startup_done and not self._running:
            raise RuntimeError("Startup sequence not completed")

        raw_frame = MidCodec.encode(mid_obj)

        async with self._lock:
            if len(mid_obj.expected_response_mids) == 0:
                raise ValueError(
                    f"The message doesn't have expected response: {mid_obj.MID}"
                )
            fut = asyncio.get_running_loop().create_future()
            self._pending_future = fut
            self._pending_expected = mid_obj.expected_response_mids
            await self._transport.send(raw_frame)

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self._pending_future = None
            self._pending_expected = set()

    async def _listener_loop(self) -> None:
        """Single receive loop: dispatch replies and events."""
        while self._running:
            try:
                raw = await self._transport.receive()
                mid_obj = MidCodec.decode(raw)

                if (
                    self._pending_future
                    and not self._pending_future.done()
                    and (
                        mid_obj.MID in self._pending_expected
                        or mid_obj.MESSAGE_TYPE == MessageType.REQ_REPLY_MESSAGE
                        or mid_obj.MESSAGE_TYPE == MessageType.OP_COMMAND
                    )
                ):
                    self._pending_future.set_result(mid_obj)
                    continue

                logger.warning(f"Not expected message: {mid_obj.MID}")
                self._pending_future.set_exception(
                    ValueError(f"Not expected response message {mid_obj.MID}")
                )
            except asyncio.CancelledError:
                logger.info("Cancelled loop")
                break
            except ValueError as e:
                logger.warning(f"Invalid message: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected exception: {e}")
                await asyncio.sleep(1)
