"""
WiFi Hotspot Creator - Linux
Creates an open (no-password) access point using NetworkManager (nmcli).
Requires: nmcli installed (standard on most distros), run with sudo or as root.

Install NetworkManager if missing:
  sudo apt install network-manager     # Debian/Ubuntu
  sudo dnf install NetworkManager      # Fedora
"""

import subprocess
import sys
import os

CON_NAME = "FRND-Hotspot"


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def check_nmcli():
    _, _, code = run("which nmcli")
    if code != 0:
        print(" nmcli not found. Install NetworkManager first.")
        sys.exit(1)


def get_wifi_interface():
    out, _, _ = run("nmcli -t -f DEVICE,TYPE device | grep ':wifi' | cut -d: -f1")
    interfaces = out.splitlines()
    if not interfaces:
        print(" No WiFi interface found.")
        sys.exit(1)
    return interfaces[0]


def start_hotspot(ssid: str, interface: str = None):
    if not interface:
        interface = get_wifi_interface()

    print(f"\n Starting open hotspot on interface: {interface}")
    print(f"   SSID: {ssid}  (no password)")

    # Remove any leftover connection with the same name
    run(f'nmcli con delete "{CON_NAME}" 2>/dev/null')

    # Create the AP connection profile
    _, err, code = run(
        f'nmcli con add type wifi ifname {interface} con-name "{CON_NAME}" '
        f'ssid "{ssid}" mode ap ipv4.method shared'
    )
    if code != 0:
        print(f" Failed to create hotspot profile:\n{err}")
        print("\n Tips:")
        print("  - Run as sudo/root")
        print("  - Make sure WiFi is not connected to another network")
        print("  - Try: sudo nmcli radio wifi on")
        sys.exit(1)

    # Clear security so the network is open
    run(f'nmcli con modify "{CON_NAME}" wifi-sec.key-mgmt ""')

    # Bring it up
    _, err, code = run(f'nmcli con up "{CON_NAME}"')
    if code != 0:
        print(f" Failed to start hotspot:\n{err}")
        sys.exit(1)

    print("\n Open hotspot is active! Anyone nearby can connect without a password.")
    print("\nTo see connected clients:")
    print("  ip neigh show")
    print("\nTo stop the hotspot, run this script and choose option 2.")


def stop_hotspot():
    _, err, code = run(f'nmcli con down "{CON_NAME}"')
    if code == 0:
        print(f" Hotspot stopped.")
    else:
        print(f" No active hotspot found or could not stop it:\n{err}")


def show_status():
    print("\n--- Active Connections ---")
    out, _, _ = run("nmcli connection show --active")
    print(out or "No active connections.")

    print("\n--- Connected Clients (ARP table) ---")
    out, _, _ = run("ip neigh show")
    print(out or "No entries.")


def show_qr(ssid: str):
    """Print a QR code for easy mobile scanning (open network format)."""
    wifi_string = f"WIFI:T:nopass;S:{ssid};;"
    _, _, code = run("which qrencode")
    if code == 0:
        run(f'qrencode -t UTF8 "{wifi_string}"')
    else:
        print(f"\n WiFi connect string (use a QR generator app):\n{wifi_string}")


if __name__ == "__main__":
    if sys.platform == "win32":
        print(" This script is for Linux only. Use hotspot_windows.py on Windows.")
        sys.exit(1)

    check_nmcli()

    print("=== WiFi Hotspot Manager (Linux) ===")
    print("1. Start open hotspot")
    print("2. Stop hotspot")
    print("3. Show status / connected clients")
    choice = input("\nSelect option (1/2/3): ").strip()

    if choice == "1":
        ssid = input("Enter SSID (network name) [default: FRND]: ").strip() or "FRND"
        iface = input("WiFi interface (leave blank to auto-detect, e.g. wlan0): ").strip() or None
        start_hotspot(ssid, iface)
        show_qr(ssid)
    elif choice == "2":
        stop_hotspot()
    elif choice == "3":
        show_status()
    else:
        print("Invalid option.")
