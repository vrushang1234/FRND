import asyncio
import threading
import http.server
import socketserver
from websockets.asyncio.server import serve
import os

# --- PART 1: THE WEB SERVER (Port 80) ---
# Running on Port 80 means the client just types the IP (no :8000)
PORT_WEB = 5173

def run_web_server():
    # This serves the ENTIRE folder (HTML, CSS, JS from the FRND repo)
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", PORT_WEB), handler) as httpd:
            print(f"🌍 FRND Web UI hosting on port {PORT_WEB}")
            httpd.serve_forever()
    except PermissionError:
        print("❌ Error: Port 5173 requires 'sudo python server.py'")

# --- PART 2: THE WEBSOCKET RELAY (Port 8376) ---
connections = set()

async def relay(websocket):
    connections.add(websocket)
    try:
        async for message in websocket:
            # Relay the message from Client to Emergency (or vice versa)
            for conn in connections:
                if conn != websocket:
                    await conn.send(message)
    finally:
        connections.remove(websocket)

async def main():
    # Start the Web Server thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Start the WebSocket Server
    async with serve(relay, "0.0.0.0", 8376) as server:
        print("💬 WebSocket Relay active on port 8376")
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
    

wat is the https address my hoen shoudl be able to go to