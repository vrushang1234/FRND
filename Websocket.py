import asyncio
import threading
import http.server
import socketserver
from websockets.asyncio.server import serve

# --- PART 1: THE WEB SERVER (Port 8000) ---
def run_web_server():
    handler = http.server.SimpleHTTPRequestHandler
    # This serves whatever is in the current folder
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print(" Web UI available at http://localhost:8000")
        httpd.serve_forever()

# --- PART 2: THE WEBSOCKET SERVER (Port 8376) ---
connections = set()

async def chat_relay(websocket):
    connections.add(websocket)
    try:
        async for message in websocket:
            # Send to everyone else
            for conn in connections:
                if conn != websocket:
                    await conn.send(message)
    finally:
        connections.remove(websocket)

async def run_ws_server():
    async with serve(chat_relay, "0.0.0.0", 8376) as server:
        print("WebSocket Relay active on port 8376")
        await server.serve_forever()

if __name__ == "__main__":
    # Start the Web Server in a separate thread so it doesn't block
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Start the WebSocket Server in the main loop
    asyncio.run(run_ws_server())



    