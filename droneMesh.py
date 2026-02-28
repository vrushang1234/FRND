import asyncio
import websockets
import json
import time
import random
import subprocess
from hotspot_linux import start_hotspot, run, get_wifi_interface

# --- CONFIGURATION ---
SSID = "Spider-Net-Mesh"   
PASSWORD = "spiderman2mesh"
# In nmcli hotspot mode, the host (Hub) always defaults to .1
HUB_IP = "192.168.4.1"    #NEED TO CHANGE THIS TO THE IP OF THE FIRST DRONE RASBERRY 

def check_for_mesh():
    """Checks if the Spider-Net SSID is currently broadcasting."""
    # Uses the run function from your hotspot_linux.py to check nmcli
    stdout, _, _ = run(f"nmcli -t -f SSID dev wifi | grep '^{SSID}$'")
    return len(stdout) > 0

def connect_to_mesh():
    """Attempts to join the existing mesh as a client."""
    print(f"🕸️ Mesh detected. Joining {SSID}...")
    # Use nmcli to connect as a standard WiFi station
    _, _, code = run(f"nmcli device wifi connect {SSID} password {PASSWORD}")
    return code == 0

# --- WEBSOCKET LOGIC ---
async def handle_telemetry(websocket, path=None):
    """Server-side: Receives data from other drones."""
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"📡 DATA FROM {data['drone_id']}: Alt {data['alt']}m | Bat {data['bat']}%")
        except Exception as e:
            print(f"Error parsing JSON: {e}")

async def send_telemetry():
    """Client-side: Sends our data to whoever is currently the Hub."""
    uri = f"ws://{HUB_IP}:8765"
    while True:
        try:
            async with websockets.connect(uri, timeout=5) as ws:
                payload = {
                    "drone_id": f"Drone-{random.randint(10,99)}", 
                    "alt": random.randint(20, 100), 
                    "bat": random.randint(50, 99)
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(2)
        except Exception:
            # If connection fails, the Hub might be gone. Exit to re-trigger scan.
            print("🚨 Lost connection to Hub. Returning to scan mode...")
            return 

# --- MAIN CONTROL LOOP ---
async def main():
    while True:
        if check_for_mesh():
            if connect_to_mesh():
                print("✅ Connected as Node. Starting Telemetry...")
                # Start acting as a client
                await send_telemetry()
            else:
                print("❌ Connection failed. Retrying...")
                await asyncio.sleep(2)
        else:
            # NO MESH FOUND: Randomized 'Election' Timer
            # This prevents all drones from starting a hotspot at the same time
            wait = random.uniform(5, 12)
            print(f"☁️ No mesh found. Waiting {wait:.1f}s to see if another drone takes lead...")
            await asyncio.sleep(wait)
            
            # Re-check: Did someone else start the mesh while we waited?
            if not check_for_mesh():
                print("🚀 TAKING THE LEAD: Starting Hotspot...")
                # Runs your start_hotspot function from hotspot_linux.py
                start_hotspot(SSID, PASSWORD) 
                
                # As the new Hub, start the WebSocket server to listen to others
                print(f"🕸️ Hub Active. Listening for peers on {HUB_IP}:8765")
                async with websockets.serve(handle_telemetry, "0.0.0.0", 8765):
                    await asyncio.Future() # Keeps the server running forever

if __name__ == "__main__":
    try:
        # Initial check to make sure WiFi is on
        run("nmcli radio wifi on")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping Spider-Node...")