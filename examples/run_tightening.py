import asyncio
import argparse
from openprotocol.application.client import OpenProtocolClient
from openprotocol.application.parameter_set import SelectParameterSet
from openprotocol.application.tightening import LastTighteningResultDataSubscribe


async def main(host, port, pset):
    # Create client
    client = OpenProtocolClient.create(host, port)

    try:
        await client.connect()
        print(f"Connected to controller at {host}:{port}")

        # Send PSET request
        pset_msg = SelectParameterSet(pset)
        response = await client.send_receive(pset_msg)
        print(f"Pset Response: {response}")

        # Example: subscribe to asynchronous event
        await client.subscribe(LastTighteningResultDataSubscribe)
        event_msg = await client.get_subscription()
        print(f"Received Event: {event_msg}")

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Cleanly disconnect
        await client.disconnect()
        print("Client disconnected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenProtocol Client")

    parser.add_argument(
        "--host", type=str, default="192.168.0.100", help="Controller IP address"
    )
    parser.add_argument("--port", type=int, default=4545, help="Controller TCP port")
    parser.add_argument("--pset", type=int, default=3, help="Parameter Set Number")

    args = parser.parse_args()

    asyncio.run(main(args.host, args.port, args.pset))
