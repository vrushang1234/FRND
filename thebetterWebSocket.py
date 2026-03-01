import asyncio
from websockets.asyncio.server import serve

# Global State
arduino_hub = None  
rooms = {}  # { "room_id": websocket_object }
message_queue = asyncio.Queue()
active_room = None # Tracks which room the Arduino is currently answering

async def relay(websocket):
    global arduino_hub, active_room
    
    client_ip = websocket.remote_address[0]
    path = websocket.request.path.strip("/")
    room_id = path if path else f"user_{client_ip.replace('.', '_')}"

    # --- 1. ASSIGN THE ARDUINO (FIRST CONNECTED) ---
    if arduino_hub is None:
        arduino_hub = websocket
        print(f"🚨 ARDUINO CONNECTED: Assigned as Emergency Services")
        
        # Start the background processor to feed the Arduino messages
        asyncio.create_task(process_queue())

        try:
            async for message in websocket:
                # When the Arduino sends a Gemini response, 
                # we send it to the 'active_room' currently being helped.
                if active_room in rooms:
                    await rooms[active_room].send(message)
                    print(f"✅ Response sent to {active_room}")
                    # Release the lock so the next person in line can talk
                    active_room = None 
                else:
                    print("⚠️ Arduino sent a message but no room is currently 'Active'.")
        finally:
            arduino_hub = None
            print("🚨 Arduino Disconnected!")
        return

    # --- 2. THE CLIENTS (PHONES/LAPTOPS) ---
    rooms[room_id] = websocket
    print(f"👤 New Client in Room: [{room_id}]")

    try:
        async for message in websocket:
            # Add the message to the queue along with its room ID
            await message_queue.put((room_id, message))
            print(f"📥 Message from [{room_id}] added to queue.")
            
            # Optional: Tell the user they are in line
            await websocket.send("System: Your message is being processed by Gemini...")

    except Exception as e:
        print(f"⚠️ Room {room_id} error: {e}")
    finally:
        if room_id in rooms:
            del rooms[room_id]
        print(f"❌ Client left {room_id}")

async def process_queue():
    """Feeds the Arduino one message at a time so it doesn't get confused."""
    global arduino_hub, active_room
    
    while True:
        # Wait for a message to appear in the queue
        target_room_id, text = await message_queue.get()
        
        if arduino_hub:
            # Lock the Arduino to this specific room
            active_room = target_room_id
            
            # Send the raw text to the Arduino (Gemini)
            await arduino_hub.send(text)
            
            # Wait for the Arduino to finish its response. 
            # The 'relay' function sets active_room to None when the reply comes back.
            while active_room is not None:
                await asyncio.sleep(0.1)
        
        message_queue.task_done()

async def main():
    async with serve(relay, "0.0.0.0", 8080):
        print("💬 Pi Relay Active on port 8080")
        print("💡 Connect your Arduino Q Board FIRST.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())