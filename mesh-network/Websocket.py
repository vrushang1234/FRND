import asyncio
import json
from websockets.asyncio.server import serve

# Global State
arduino_hub = None  
rooms = {}  # { "room_id": websocket_object }
room_histories = {} # { "room_id": [list of message dicts] }
message_queue = asyncio.Queue()
active_room = None 

async def relay(websocket):
    global arduino_hub, active_room
    
    client_ip = websocket.remote_address[0]
    path = websocket.request.path.strip("/")
    room_id = path if path else f"user_{client_ip.replace('.', '_')}"

    # --- 1. ASSIGN THE ARDUINO HUB ---
    if arduino_hub is None:
        arduino_hub = websocket
        print(f"🚨 ARDUINO HUB CONNECTED: Setting up Brain...")
        
        asyncio.create_task(process_queue())

        try:
            async for message in websocket:
                # The Arduino returns a JSON containing a summary and a response
                try:
                    resp_data = json.loads(message)
                    if active_room in rooms:
                        # Send the AI response back to the specific drone node
                        await rooms[active_room].send(json.dumps(resp_data))
                        
                        # Add the AI's response to the history so it remembers what it said
                        room_histories[active_room].append({"role": "AI", "content": resp_data.get("response")})
                        
                        print(f"✅ Contextual Response sent to {active_room}")
                        active_room = None 
                except json.JSONDecodeError:
                    print("⚠️ Hub sent non-JSON data.")
        finally:
            arduino_hub = None
            print("🚨 Arduino Disconnected!")
        return

    # --- 2. THE NODES (DRONES/CLIENTS) ---
    rooms[room_id] = websocket
    if room_id not in room_histories:
        room_histories[room_id] = [] # Initialize history for new rooms
        
    print(f"👤 New Node in Room: [{room_id}]")

    try:
        async for message in websocket:
            # 1. Update the history with the new message
            room_histories[room_id].append({"role": "Node", "content": message})
            
            # 2. Add the room_id to the queue
            await message_queue.put(room_id)
            print(f"📥 Interaction from [{room_id}] queued for summary.")
            
            await websocket.send("System: Brain is processing full conversation history...")

    except Exception as e:
        print(f"⚠️ Room {room_id} error: {e}")
    finally:
        if room_id in rooms:
            del rooms[room_id]
        print(f"❌ Node left {room_id}")

async def process_queue():
    """Feeds the Hub the ENTIRE JSON history for the room."""
    global arduino_hub, active_room
    
    while True:
        target_room_id = await message_queue.get()
        
        if arduino_hub:
            active_room = target_room_id
            
            # Prepare the Context Packet
            context_packet = {
                "room_id": target_room_id,
                "history": room_histories[target_room_id],
                "node_count": len(rooms)
            }
            
            # Send the entire JSON string to the Arduino
            await arduino_hub.send(json.dumps(context_packet))
            
            # Wait for the AI to return the summary/response
            while active_room is not None:
                await asyncio.sleep(0.1)
        
        message_queue.task_done()

async def main():
    # We use 0.0.0.0 to listen on all interfaces, including the hotspot
    async with serve(relay, "0.0.0.0", 8080):
        print("💬 Spider-Net Relay Active on port 8080")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
