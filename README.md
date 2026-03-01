
# FRND — Field Relay Neighboring Datapoints

> A peer-to-peer emergency communication network that works when traditional infrastructure fails.

## Overview

FRND is an emergency communication system designed to connect stranded individuals with rescue teams when cellular service is unavailable. Using a swarm of drone-deployed Raspberry Pi nodes forming a mesh WiFi network, combined with an AI-powered Arduino UNO Q, FRND enables real-time, intelligent communication at the edge — no internet required.

## The Problem

In disaster scenarios — wildfires, earthquakes, floods — cellular infrastructure is often the first thing to go. Victims have no way to reach emergency services, and rescue teams have no way to coordinate. FRND solves this by creating a self-contained communication network that can be deployed from the air.

## How It Works

### Mesh Network
Each Raspberry Pi node uses the Linux Network Manager (`nmcli`) to operate as a WiFi access point, forming a multi-nodal mesh network from the ground up — no external routers needed. Drones deploy these nodes into disaster zones, creating coverage where none exists.

### Communication Layer
WebSocket-based messaging (built with Python's `websockets` and `asyncio` libraries) handles real-time communication between:
- **Victims** — connecting via any WiFi-enabled device
- **Rescue teams** — monitoring and responding through a dedicated interface
- **The AI node** — an Arduino UNO Q providing intelligent, automated support

Concurrent multi-client communication is supported, allowing multiple victims and responders to communicate simultaneously.

### Edge AI
The Arduino UNO Q runs a local LLM entirely on-device using [yzma](https://github.com/hybridgroup/yzma) (a Go wrapper for llama.cpp). This means:
- **No cloud connectivity required** — inference runs on the board's ARM processor
- **Auto-responses** to victim messages when rescue teams are overwhelmed
- **Urgency detection** to alert rescue teams to critical situations
- **Structured information gathering** — injuries, location, number of people

## Repository Structure

```
FRND/
├── emergency-terminal/   # Rescue team interface
├── frnd-terminal/        # Victim-facing communication interface  
└── mesh-network/         # Raspberry Pi mesh network setup
```

## Tech Stack

| Component | Technology |
|---|---|
| Mesh Network | Raspberry Pi + nmcli |
| Communication | Python WebSockets + asyncio |
| Edge AI | Arduino UNO Q + yzma + llama.cpp |
| LLM Model | SmolLM2-135M-Instruct (quantized GGUF) |
| Frontend | JavaScript / HTML / CSS |

## Hardware

- **Arduino UNO Q** (4GB or 2GB) — AI inference node
- **Raspberry Pi** (multiple) — mesh network nodes
- **Drone** — for aerial deployment of network nodes

## Getting Started

### Mesh Network Setup
```bash
cd mesh-network
# Follow setup instructions for Raspberry Pi access point configuration
```

### Running the AI Node (Arduino UNO Q)
```bash
# Install Go and yzma
sudo apt install golang
go install github.com/hybridgroup/yzma/cmd/yzma@v1.9.0
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc && source ~/.bashrc

# Install llama.cpp libraries
export YZMA_LIB=/home/arduino/FRND/yzma/lib
yzma install -u --processor cpu --os trixie

# Download model
yzma model get -u https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_K_M.gguf

# Run
cd /home/arduino/FRND/yzma
go run ./examples/chat/ -model ~/models/SmolLM2-135M-Instruct-Q4_K_M.gguf -lib ./lib/ -v
```

### Running the WebSocket Server
```bash
cd mesh-network
python3 server.py
```

## Why FRND?

Traditional emergency communication breaks down exactly when it's needed most. FRND is built on the principle that **every node in the network should be capable of independent, intelligent operation**. Even the smallest node — the Arduino UNO Q — carries enough AI capability to guide a victim through a crisis without any external support.

FRND doesn't wait for infrastructure to be restored. It brings the infrastructure with it.
