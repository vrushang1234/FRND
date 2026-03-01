import os
import asyncio
import websockets
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Gemini connected!")

async def handle(websocket):
    print("Pi connected!")

    async for message in websocket:
        print("Question: " + message)

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=message
            )
            reply = response.text
            print("Answer: " + reply[:100] + "...")
        except Exception as e:
            reply = "Sorry, Gemini error: " + str(e)
            print(reply)

        await websocket.send(reply)

async def main():
    print("Gemini server running on port 8765...")
    async with websockets.serve(handle, "0.0.0.0", 8765, ping_timeout=120):
        await asyncio.Future()

asyncio.run(main())