import asyncio
from websockets.asyncio.server import serve

connections = set()

async def relay(websocket):
    connections.add(websocket)

    client_ip = websocket.remote_address[0]
    print(f"🔌 Client connected: {client_ip}")

    try:
        async for message in websocket:
            print(f" From {client_ip}: {message}")

            # Relay to other clients
            for conn in list(connections):
                if conn != websocket:
                    await conn.send(message)

    except Exception as e:
        print(f" Error from {client_ip}: {e}")

    finally:
        connections.discard(websocket)
        print(f" Client disconnected: {client_ip}")


async def main():
    async with serve(relay, "0.0.0.0", 8080):
        print(" WebSocket Relay active on port 8080")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
