import asyncio
from openprotocol.core.mid_base import MidCodec
from openprotocol.transport.base import BaseTransport


class AsyncTcpClient(BaseTransport):
    """TCP client for Open Protocol transport layer (raw frames)."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self, timeout: float = 5.0):
        """Establish TCP connection with timeout."""
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=timeout
            )
        except asyncio.TimeoutError:
            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port} (timeout)"
            )
        except Exception as e:
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}: {e}")

        if self.reader is None or self.writer is None:
            raise ConnectionError(f"Connection failed to {self.host}:{self.port}")

    def _ensure_connected(self):
        if not self.reader or not self.writer:
            raise ConnectionError("The client is not connected")

    async def _read_frame(self, timeout: float) -> bytes:
        """Read one full Open Protocol frame."""
        length_bytes = await asyncio.wait_for(
            self.reader.readexactly(MidCodec.LENGTH_FIELD_SIZE), timeout
        )
        frame_length = int(length_bytes.decode("ascii"))
        remaining = await asyncio.wait_for(
            self.reader.readexactly(frame_length - MidCodec.LENGTH_FIELD_SIZE),
            timeout,
        )
        return length_bytes + remaining

    async def send_receive(self, data: bytes, timeout: float = 5.0) -> bytes:
        """Send a frame and wait for a full response."""
        await self.send(data)
        return await self.receive(timeout)

    async def send(self, data: bytes):
        """Send a frame without waiting for a response."""
        self._ensure_connected()
        self.writer.write(data)
        await self.writer.drain()

    async def receive(self, timeout: float = 5.0) -> bytes:
        """Receive a full frame."""
        self._ensure_connected()
        return await self._read_frame(timeout)

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
