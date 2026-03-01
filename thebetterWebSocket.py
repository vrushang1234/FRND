import asyncio
import json
from websockets.asyncio.server import serve

# Global State
arduino_client = None  
rooms = {}  # { "room_id": websocket_object }

async def relay(websocket):
    global arduino_client
    
    client_ip = websocket.remote_address[0]
    path = websocket.request.path.strip("/")
    room_id = path if path else f"user_{client_ip.replace('.', '_')}"

    # --- 1. IDENTIFY ARDUINO ---
    # (Assuming the Arduino connects with a specific path or is the first connection)
    if path == "arduino":
        arduino_client = websocket
        print(f"🚨 ARDUINO BRAIN CONNECTED")
        try:
            async for raw_message in websocket:
                # Arduino sends: {"room": "room1", "msg": "Hello"}
                data = json.loads(raw_message)
                target = data.get("room")
                if target in rooms:
                    await rooms[target].send(data.get("msg"))
        finally:
            arduino_client = None
        return

    # --- 2. IDENTIFY PHONES ---
    rooms[room_id] = websocket
    print(f"👤 Phone joined: {room_id}")

    try:
        async for message in websocket:
            if arduino_client:
                # Wrap message in JSON for the Arduino
                payload = json.dumps({
                    "room": room_id,
                    "msg": message
                })
                await arduino_client.send(payload)
            else:
                await websocket.send("System: Emergency Brain is offline.")
    finally:
        if room_id in rooms:
            del rooms[room_id]

async def main():
    async with serve(relay, "0.0.0.0", 8765):
        print("💬 Pi JSON Relay Active on port 8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
