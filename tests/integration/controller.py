import asyncio
from typing import Optional

from openprotocol.application import CommunicationPositiveAck
from openprotocol.application.communication import (
    CommunicationStartMessage,
    CommunicationStopMessage,
    CommunicationStartAcknowledge,
)
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage, MidCodec, register_messages


class CommunicationStartAcknowledgeController(CommunicationStartAcknowledge):
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        msg = list(" " * 42)
        msg[0:2] = "01"
        msg[2:6] = str(self._cell_id).zfill(4)
        msg[6:8] = "02"
        msg[8:10] = str(self._channel_id).zfill(2)
        msg[10:12] = "03"
        msg[12:37] = self._controller_name.ljust(37 - 12)
        msg[37:39] = "04"
        msg[39:42] = self._supplier_code.ljust(39 - 42)
        return self.create_message(self.REVISION, "".join(msg))


class CommunicationPositiveAckController(CommunicationPositiveAck):
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        payload = str(self._mid).zfill(4)
        msg = self.create_message(self.REVISION, payload)
        return msg


register_messages(CommunicationStartMessage, CommunicationStopMessage)


class SimulatedController:
    """Async simulated OpenProtocol controller for integration testing."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        self.host = host
        self.port = port
        self._server: Optional[asyncio.AbstractServer] = None
        self._expected: list[tuple[int, int, str]] = []  # (MID, REV, raw_response)
        self._connections: list[tuple[asyncio.StreamReader, asyncio.StreamWriter]] = []
        self._set_connection_start_support()

    def _set_connection_start_support(self):
        resp = CommunicationStartAcknowledgeController(1, 1, 1, "Testing", "001")
        self.expect(
            CommunicationStartMessage.MID,
            CommunicationStartMessage.REVISION,
            resp.encode(),
        )
        self.expect(
            CommunicationStopMessage.MID,
            CommunicationStopMessage.REVISION,
            CommunicationPositiveAckController(
                1, CommunicationStopMessage.MID
            ).encode(),
        )

    async def start(self):
        """Start listening server."""
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        print(f"Simulated controller listening on {self.host}:{self.port}")

    async def stop(self):
        """Stop server and close connections."""
        for _, writer in self._connections:
            writer.close()
            await writer.wait_closed()
        self._connections.clear()

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            print("Simulated controller stopped.")

    def expect(
        self,
        mid: int,
        revision: int = 1,
        respond_with: Optional[OpenProtocolRawMessage] = None,
    ):
        """Define expected MID and what to respond with."""
        if respond_with:
            raw = respond_with.raw_str
        else:
            raw = b""
        self._expected.append((mid, revision, raw))

    async def push_event(self, event_msg: OpenProtocolMessage):
        """Push event to all connected clients."""
        if not self._connections:
            return
        raw = MidCodec.encode(event_msg)
        for _, writer in self._connections:
            writer.write(raw)
            await writer.drain()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle one connected client."""
        self._connections.append((reader, writer))
        try:
            while True:
                # Read frame length first
                length_bytes = await reader.readexactly(4)
                frame_length = int(length_bytes.decode("ascii"))
                remaining = await reader.readexactly(frame_length - 4)
                raw = length_bytes + remaining

                msg = MidCodec.decode(raw)
                print(f"Controller received MID={msg.MID}")

                # Find matching expectation
                for mid, rev, raw_resp in self._expected:
                    if msg.MID == mid and msg.REVISION == rev:
                        if raw_resp:
                            writer.write(raw_resp.encode("ascii"))
                            await writer.drain()
                        break
                else:
                    print(f"Unexpected MID {msg.MID}, ignoring...")

        except asyncio.IncompleteReadError:
            print("Client disconnected.")
        finally:
            print("Client closed.")
            writer.close()
            await writer.wait_closed()
