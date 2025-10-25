import asyncio

import pytest

from openprotocol.application.client import OpenProtocolClient
from openprotocol.application.parameter_set import SelectParameterSet
from tests.integration.controller import SimulatedController


@pytest.mark.asyncio
async def test_client_startup_sequence():
    controller = SimulatedController(port=9999)
    await controller.start()

    client = OpenProtocolClient.create("127.0.0.1", 9999)
    await client.connect()

    await asyncio.sleep(0.2)

    res = await client.disconnect()
    assert res
    await controller.stop()


@pytest.mark.asyncio
async def test_client_disconnect_controller():
    controller = SimulatedController(port=9999)
    await controller.start()

    client = OpenProtocolClient.create("127.0.0.1", 9999)
    await client.connect()

    await asyncio.sleep(0.2)
    await controller.stop()
    assert not await client.send_receive(SelectParameterSet(3))
