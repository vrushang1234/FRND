"""
WiFi Hotspot Creator - Linux
Creates an access point using NetworkManager (nmcli).
Requires: nmcli installed (standard on most distros), run with sudo or as root.

Install NetworkManager if missing:
  sudo apt install network-manager     # Debian/Ubuntu
  sudo dnf install NetworkManager      # Fedora
"""

import subprocess
import sys
import os


def run(cmd, check=False):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def check_nmcli():
    _, _, code = run("which nmcli")
    if code != 0:
        print("❌ nmcli not found. Install NetworkManager first.")
        sys.exit(1)


def get_wifi_interface():
    out, _, _ = run("nmcli -t -f DEVICE,TYPE device | grep ':wifi' | cut -d: -f1")
    interfaces = out.splitlines()
    if not interfaces:
        print("❌ No WiFi interface found.")
        sys.exit(1)
    return interfaces[0]


def start_hotspot(ssid: str, password: str, interface: str = None):
    if not interface:
        interface = get_wifi_interface()

    print(f"\n📡 Starting hotspot on interface: {interface}")
    print(f"   SSID    : {ssid}")
    print(f"   Password: {password}")

    cmd = (
        f'nmcli device wifi hotspot '
        f'ifname {interface} '
        f'ssid "{ssid}" '
        f'password "{password}"'
    )

    out, err, code = run(cmd)
    if code != 0:
        print(f"❌ Failed to start hotspot:\n{err}")
        print("\n💡 Tips:")
        print("  - Run as sudo/root")
        print("  - Make sure WiFi is not connected to another network")
        print("  - Try: sudo nmcli radio wifi on")
        sys.exit(1)

    print("\n✅ Hotspot is active! Others can connect now.")
    print("\nTo see connected clients:")
    print("  ip neigh show")
    print("\nTo stop the hotspot, run this script and choose option 2.")


def stop_hotspot():
    out, err, code = run("nmcli connection show --active | grep Hotspot | awk '{print $1}'")
    if not out:
        print("⚠️  No active hotspot found.")
        return

    hotspot_name = out.splitlines()[0]
    _, err, code = run(f'nmcli connection down "{hotspot_name}"')
    if code == 0:
        print(f"✅ Hotspot '{hotspot_name}' stopped.")
    else:
        print(f"❌ Could not stop hotspot:\n{err}")


def show_status():
    print("\n--- Active Connections ---")
    out, _, _ = run("nmcli connection show --active")
    print(out or "No active connections.")

    print("\n--- Connected Clients (ARP table) ---")
    out, _, _ = run("ip neigh show")
    print(out or "No entries.")


def show_qr(ssid: str, password: str):
    """Print a QR code string for easy mobile scanning (requires qrencode)."""
    wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    _, _, code = run(f'which qrencode')
    if code == 0:
        run(f'qrencode -t UTF8 "{wifi_string}"')
    else:
        print(f"\n📋 WiFi connect string (use a QR generator app):\n{wifi_string}")


if __name__ == "__main__":
    if sys.platform == "win32":
        print("❌ This script is for Linux only. Use hotspot_windows.py on Windows.")
        sys.exit(1)

    check_nmcli()

    print("=== WiFi Hotspot Manager (Linux) ===")
    print("1. Start hotspot")
    print("2. Stop hotspot")
    print("3. Show status / connected clients")
    choice = input("\nSelect option (1/2/3): ").strip()

    if choice == "1":
        ssid = input("Enter SSID (network name) [default: MyHotspot]: ").strip() or "MyHotspot"
        password = input("Enter password (min 8 chars): ").strip()
        if len(password) < 8:
            print("❌ Password must be at least 8 characters.")
            sys.exit(1)
        iface = input("WiFi interface (leave blank to auto-detect, e.g. wlan0): ").strip() or None
        start_hotspot(ssid, password, iface)
        show_qr(ssid, password)
    elif choice == "2":
        stop_hotspot()
    elif choice == "3":
        show_status()
    else:
        print("Invalid option.")
