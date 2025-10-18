import asyncio

import pytest

from openprotocol.application.base_messages import CommunicationPositiveAck
from openprotocol.application.client import OpenProtocolClient
from openprotocol.application.communication import (
    CommunicationStartMessage,
    CommunicationStartAcknowledge,
    CommunicationStopMessage,
)
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import register_messages
from tests.integration.controller import SimulatedController


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

@pytest.mark.asyncio
async def test_client_startup_sequence():
    controller = SimulatedController(port=9999)
    await controller.start()

    resp = CommunicationStartAcknowledgeController(1, 1, 1, "Testing", "001")
    controller.expect(
        CommunicationStartMessage.MID, CommunicationStartMessage.REVISION, resp.encode()
    )
    controller.expect(
        CommunicationStopMessage.MID,
        CommunicationStopMessage.REVISION,
        CommunicationPositiveAckController(1, CommunicationStopMessage.MID).encode(),
    )

    client = OpenProtocolClient.create("127.0.0.1", 9999)
    await client.connect()

    await asyncio.sleep(0.2)

    await client.disconnect()
    await controller.stop()
