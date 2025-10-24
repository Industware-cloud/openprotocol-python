import asyncio

import pytest

from openprotocol.application import CommunicationPositiveAck
from openprotocol.application.base_messages import OpenProtocolEvent
from openprotocol.application.client import OpenProtocolClient
from openprotocol.application.parameter_set import SelectParameterSet
from openprotocol.application.tightening import (
    LastTighteningResultDataSubscribe,
    LastTighteningResultData,
)
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import register_messages, OpenProtocolMessage
from tests.integration.controller import (
    SimulatedController,
    CommunicationPositiveAckController,
)


class SelectParameterSetController(SelectParameterSet):

    def __init__(self, id_set: int):
        super().__init__(id_set)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        id_set = int(msg.payload[0:4])
        return cls(id_set)


class TighteningDevice(OpenProtocolEvent):
    MID = 61
    REVISION = 1

    def __init__(self, revision: int | None = None):
        self._revision: int = revision or TighteningDevice.REVISION
        super().__init__(self._revision)

    def encode(self) -> OpenProtocolRawMessage:
        payload = list(" " * 175)
        payload[0:2] = "01"
        payload[2:6] = "0001"  # cell_id 23-26
        payload[6:8] = "02"
        payload[8:10] = "01"  # channel_id 29-30
        payload[10:12] = "03"
        payload[12:37] = "Test controller".ljust(
            37 - 12
        )  # 33-57 torque_controller_name
        payload[70:73] = "001"  # pset_number 91-93
        payload[85:87] = "09"
        payload[87:88] = "1"  ## tightening_status 108
        payload[88:90] = "10"
        payload[90:91] = "1"  # torque_status 111 (0=Low,1=OK,2=High)
        payload[93:94] = "1"  # 114 angle_status (0=Low,1=OK,2=High)
        payload[120:126] = "000120"  # torque 141-146
        payload[156:175] = "YYYY-MM-DD:HH:MM:SS"  # timestamp
        return self.create_message(self._revision, "".join(payload))

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        raise NotImplementedError()


register_messages(SelectParameterSetController, LastTighteningResultDataSubscribe)


@pytest.mark.asyncio
async def test_tightening_flow():
    controller = SimulatedController(port=9999)
    await controller.start()

    client = OpenProtocolClient.create("127.0.0.1", 9999)
    await client.connect()

    pset_msg = SelectParameterSetController(3)
    controller.expect(
        SelectParameterSetController.MID,
        SelectParameterSetController.REVISION,
        CommunicationPositiveAckController(
            1, SelectParameterSetController.MID
        ).encode(),
    )
    controller.expect(
        LastTighteningResultDataSubscribe.MID,
        LastTighteningResultDataSubscribe.REVISION,
        CommunicationPositiveAckController(
            1, LastTighteningResultDataSubscribe.MID
        ).encode(),
    )
    response = await client.send_receive(pset_msg)
    assert isinstance(response, CommunicationPositiveAck)
    assert response.MID == CommunicationPositiveAck.MID
    assert response._mid == SelectParameterSetController.MID
    await asyncio.sleep(0.2)

    await client.subscribe(LastTighteningResultDataSubscribe)

    tightening_event = TighteningDevice()  # fill in your payload
    await controller.push_event(tightening_event)

    event = await asyncio.wait_for(client.get_subscription(), timeout=1.0)
    assert isinstance(event, LastTighteningResultData)
    assert event.tightening_status == 1

    await asyncio.sleep(0.2)
    await client.disconnect()
    await controller.stop()
