import asyncio

from openprotocol.application.client import OpenProtocolClient
from openprotocol.application.parameter_set import SelectParameterSet
from openprotocol.application.tightening import LastTighteningResultDataSubscribe


async def main():
    host = "192.168.0.100"
    port = 5000

    # Create client
    client = OpenProtocolClient.create(host, port)

    # Connect (runs startup handshake automatically)
    try:
        await client.connect()
        print("Connected to controller.")

        # Example: send a tightening request
        pset = SelectParameterSet(3)
        response = await client.send_receive(pset)
        print(f"Pset response: {response}")

        # Example: subscribe to asynchronous event
        await client.subscribe(LastTighteningResultDataSubscribe)
        event_msg = await client.get_subscription()
        print(f"Received event: {event_msg}")

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Cleanly disconnect
        await client.disconnect()
        print("Client disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
