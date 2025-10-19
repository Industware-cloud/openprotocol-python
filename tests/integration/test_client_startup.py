import asyncio

import pytest

from openprotocol.application.client import OpenProtocolClient
from tests.integration.controller import SimulatedController


@pytest.mark.asyncio
async def test_client_startup_sequence():
    controller = SimulatedController(port=9999)
    await controller.start()

    client = OpenProtocolClient.create("127.0.0.1", 9999)
    await client.connect()

    await asyncio.sleep(0.2)

    await client.disconnect()
    await controller.stop()
