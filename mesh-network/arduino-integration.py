import os
import asyncio
import websockets
import json  # <--- Added for JSON support
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Gemini connected!")

async def handle(websocket):
    print("Connected to Raspberry Pi Relay!")

    async def process_message(data_json):
        """Helper to process each Gemini request independently."""
        try:
            # 1. Parse the incoming package
            data = json.loads(data_json)
            room_id = data.get("room")
            message = data.get("msg")

            print(f"[{room_id}] Processing: {message[:50]}...")

            # 2. Call Gemini
            response = client.models.generate_content(
                model="gemini-2.0-flash", # Use 2.0 or 1.5 as 2.5 isn't out yet!
                contents=message
            )
            
            # 3. Wrap the reply back with the SAME Room ID
            reply_package = json.dumps({
                "room": room_id,
                "msg": response.text
            })
            
            # 4. Send back to Pi
            await websocket.send(reply_package)
            print(f"✅ [{room_id}] Reply sent.")

        except Exception as e:
            print(f"⚠️ Error: {e}")

    async for raw_message in websocket:
        # Create a concurrent task for every incoming message
        # This allows Phone A to start while Phone B is still generating!
        asyncio.create_task(process_message(raw_message))

async def main():
    # Note: If the Arduino is the CLIENT, it should connect TO the Pi
    # Replace 'PI_IP_ADDRESS' with your actual Raspberry Pi IP
    uri = "ws://PI_IP_ADDRESS:8765"
    async with websockets.connect(uri, ping_timeout=120) as websocket:
        await handle(websocket)

if __name__ == "__main__":
    asyncio.run(main())
