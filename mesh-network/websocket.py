import asyncio
import json
import os
from websockets.asyncio.server import serve

admin_client = None
rooms = {}  # { room_id: {"ws": websocket, "ip": client_ip, "llm_handled": bool} }
user_join_order = []  # ordered list of room_ids, oldest first

MAX_MANUAL_USERS = 2  # first N users are handled by the emergency-terminal

# ── LLM configuration ────────────────────────────────────────────────────────
# Set this to the directory you run the go command from
LLM_CWD = os.path.expanduser("~/path/to/go-llm-project")  # <-- CHANGE THIS

LLM_CMD = [
    "go", "run", "./examples/chat/",
    "-model", os.path.expanduser("~/models/SmolLM2-135M-Instruct-Q4_K_M.gguf"),
    "-lib", "./lib/",
    "-v",
]

llm_proc = None
llm_lock = asyncio.Lock()


async def ensure_llm_running():
    global llm_proc
    if llm_proc is not None and llm_proc.returncode is None:
        return  # already running

    print(" Starting LLM subprocess...")
    llm_proc = await asyncio.create_subprocess_exec(
        *LLM_CMD,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        cwd=LLM_CWD,
    )

    # Drain startup output (model loading messages) for up to 10 seconds
    try:
        while True:
            await asyncio.wait_for(llm_proc.stdout.readline(), timeout=10.0)
    except asyncio.TimeoutError:
        pass

    print(" LLM ready")


async def query_llm(message: str) -> str:
    """Send a message to the LLM subprocess and return its response."""
    async with llm_lock:
        await ensure_llm_running()

        # Send the user's message
        llm_proc.stdin.write((message + "\n").encode())
        await llm_proc.stdin.drain()

        # Read lines until output pauses for 3 seconds (response finished)
        response_lines = []
        while True:
            try:
                line = await asyncio.wait_for(
                    llm_proc.stdout.readline(), timeout=3.0
                )
                decoded = line.decode(errors="replace").rstrip()
                # Skip bare prompt characters and echoed input
                if decoded and decoded.strip() not in (">", ">>>", message.strip()):
                    response_lines.append(decoded)
            except asyncio.TimeoutError:
                break  # silence = LLM finished responding

        return "\n".join(response_lines).strip() or "I could not respond right now."


# ── WebSocket handlers ────────────────────────────────────────────────────────

async def relay(websocket):
    client_ip = websocket.remote_address[0]

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
                "llm_handled": info["llm_handled"],
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

    # Assign a unique room_id
    base = f"user_{client_ip.replace('.', '_')}"
    room_id = base
    counter = 1
    while room_id in rooms:
        room_id = f"{base}_{counter}"
        counter += 1

    # Determine if this user will be LLM-handled (3rd user onward)
    active_count = len([r for r in user_join_order if r in rooms])
    llm_handled = active_count >= MAX_MANUAL_USERS

    rooms[room_id] = {"ws": websocket, "ip": client_ip, "llm_handled": llm_handled}
    user_join_order.append(room_id)
    print(f" User joined: {room_id} ({client_ip}) — {'LLM auto-reply' if llm_handled else 'manual'}")

    if admin_client:
        try:
            await admin_client.send(json.dumps({
                "type": "user_connected",
                "id": room_id,
                "ip": client_ip,
                "llm_handled": llm_handled,
            }))
        except Exception:
            pass

    # Pre-start LLM if this is an overflow user
    if llm_handled:
        asyncio.create_task(ensure_llm_running())

    try:
        async for message in websocket:
            if llm_handled:
                # Auto-reply via LLM
                response = await query_llm(message)
                try:
                    await websocket.send(response)
                except Exception:
                    pass

                # Also forward to admin for monitoring (marked as llm reply)
                if admin_client:
                    try:
                        await admin_client.send(json.dumps({
                            "type": "message",
                            "from": room_id,
                            "content": message,
                        }))
                        await admin_client.send(json.dumps({
                            "type": "message",
                            "from": f"[LLM→{room_id}]",
                            "content": response,
                        }))
                    except Exception:
                        pass
            else:
                # Forward to emergency-terminal for manual reply
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
        if room_id in user_join_order:
            user_join_order.remove(room_id)

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
