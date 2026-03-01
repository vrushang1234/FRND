import asyncio
import json
from websockets.asyncio.server import serve

admin_client = None
rooms = {}  # { room_id: {"ws": websocket, "ip": client_ip} }


async def relay(websocket):
    client_ip = websocket.remote_address[0]

    # Wait for identify message from either admin or user
    try:
        raw = await websocket.recv()
        data = json.loads(raw)
        role = data.get("role")
    except Exception:
        return

    if role == "admin":
        await handle_admin(websocket)
    elif role == "user":
        await handle_user(websocket, client_ip)


async def handle_admin(websocket):
    global admin_client
    admin_client = websocket
    print(" EMERGENCY TERMINAL CONNECTED")

    # Catch admin up on already-connected users
    for room_id, info in list(rooms.items()):
        try:
            await websocket.send(json.dumps({
                "type": "user_connected",
                "id": room_id,
                "ip": info["ip"],
            }))
        except Exception:
            pass

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
                if data.get("type") == "message":
                    target = data.get("to")
                    content = data.get("content", "")
                    if target in rooms:
                        await rooms[target]["ws"].send(content)
            except json.JSONDecodeError:
                pass
    finally:
        if admin_client == websocket:
            admin_client = None
        print(" EMERGENCY TERMINAL DISCONNECTED")


async def handle_user(websocket, client_ip):
    global admin_client

    # Unique room_id — handle multiple users from the same IP
    base = f"user_{client_ip.replace('.', '_')}"
    room_id = base
    counter = 1
    while room_id in rooms:
        room_id = f"{base}_{counter}"
        counter += 1

    rooms[room_id] = {"ws": websocket, "ip": client_ip}
    print(f" User joined: {room_id} ({client_ip})")

    if admin_client:
        try:
            await admin_client.send(json.dumps({
                "type": "user_connected",
                "id": room_id,
                "ip": client_ip,
            }))
        except Exception:
            pass

    try:
        async for message in websocket:
            if admin_client:
                try:
                    await admin_client.send(json.dumps({
                        "type": "message",
                        "from": room_id,
                        "content": message,
                    }))
                except Exception:
                    pass
            else:
                await websocket.send("System: Emergency terminal is offline.")
    finally:
        rooms.pop(room_id, None)
        if admin_client:
            try:
                await admin_client.send(json.dumps({
                    "type": "user_disconnected",
                    "id": room_id,
                }))
            except Exception:
                pass
        print(f" User disconnected: {room_id}")


async def main():
    async with serve(relay, "0.0.0.0", 8080):
        print(" FRND WebSocket Server active on port 8080")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

