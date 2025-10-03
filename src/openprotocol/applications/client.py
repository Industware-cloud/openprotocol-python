from openprotocol.core.mid_base import OpenProtocolMid, MidCodec
from openprotocol.transport.async_tcp import AsyncTcpClient


class OpenProtocolClient:
    def __init__(self, transport: AsyncTcpClient, keepalive_interval=15.0):
        self._transport = transport

    @classmethod
    def create(cls, host: str, port: int, keepalive_interval=15.0):
        transport = AsyncTcpClient(host, port)
        return OpenProtocolClient(transport, keepalive_interval)

    async def connect(self):
        await self._transport.connect()

    async def send_receive(
        self, mid_obj: OpenProtocolMid, timeout=5.0
    ) -> OpenProtocolMid:
        raw_frame = MidCodec.encode(mid_obj)
        response_bytes = await self._transport.send_receive(raw_frame, timeout)
        msg_mid = MidCodec.decode(response_bytes)
        if (
            mid_obj.expected_response_mid is not None
            and msg_mid.MID not in mid_obj.expected_response_mid
        ):
            raise ValueError(f"Not expected response message {msg_mid.MID}")
        return msg_mid

    async def close(self):
        await self._transport.close()
