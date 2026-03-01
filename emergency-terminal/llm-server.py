"""
LLM service for emergency-terminal (runs on the admin device).

Spawns the Go LLM as a persistent subprocess and exposes a simple
HTTP API on localhost:3001 that the emergency-terminal React app calls
to get auto-replies for overflow users.

Usage:
  LLM_CWD=/path/to/go-project python llm-server.py

  Or set LLM_CWD at the top of this file.
"""

import json
import os
import select
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ── Configuration ─────────────────────────────────────────────────────────────
# Directory you normally run: go run ./examples/chat/ ... from
LLM_CWD = os.environ.get("LLM_CWD", os.path.expanduser("~/path/to/go-project"))  # CHANGE THIS

LLM_CMD = [
    "go", "run", "./examples/chat/",
    "-model", os.path.expanduser("~/models/SmolLM2-135M-Instruct-Q4_K_M.gguf"),
    "-lib", "./lib/",
    "-v",
]

PORT = int(os.environ.get("LLM_PORT", 3001))
# ──────────────────────────────────────────────────────────────────────────────

_proc = None
_lock = threading.Lock()  # ensures one LLM query at a time


def _start_llm():
    global _proc
    if _proc is not None and _proc.poll() is None:
        return
    print(" Starting LLM subprocess...")
    _proc = subprocess.Popen(
        LLM_CMD,
        cwd=LLM_CWD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    # Drain model-loading output (up to 10 seconds of startup noise)
    deadline = time.time() + 10
    while time.time() < deadline:
        ready, _, _ = select.select([_proc.stdout], [], [], 0.5)
        if ready:
            _proc.stdout.readline()
    print(" LLM ready")


def _query_llm(message: str) -> str:
    with _lock:
        _start_llm()

        _proc.stdin.write(message + "\n")
        _proc.stdin.flush()

        # Collect lines until 3 seconds of silence (LLM finished responding)
        lines = []
        while True:
            ready, _, _ = select.select([_proc.stdout], [], [], 3.0)
            if not ready:
                break  # silence = done
            line = _proc.stdout.readline().rstrip()
            # Skip bare prompts and echoed input
            if line and line.strip() not in (">", ">>>", message.strip()):
                lines.append(line)

        return "\n".join(lines).strip() or "I could not respond right now."


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/query":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        message = body.get("message", "").strip()

        if not message:
            self.send_error(400, "message required")
            return

        response = _query_llm(message)

        payload = json.dumps({"response": response}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(payload))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass  # silence request logs


if __name__ == "__main__":
    if not os.path.isdir(LLM_CWD):
        print(f"ERROR: LLM_CWD does not exist: {LLM_CWD}")
        print("Set LLM_CWD at the top of llm-server.py or via the environment variable.")
        raise SystemExit(1)

    # Pre-start the LLM so it's warm before the first user arrives
    threading.Thread(target=_start_llm, daemon=True).start()

    server = ThreadingHTTPServer(("localhost", PORT), Handler)
    print(f" LLM service on http://localhost:{PORT}")
    server.serve_forever()
