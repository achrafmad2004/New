# === RELAY SCRIPT (WebSocket Listener + TCP Tunnel to Balatro) ===
# File: relay.py

import asyncio
import websockets
import socket
import threading
import time

BALATRO_HOST = "161.35.252.15"
BALATRO_PORT = 8788
RELAY_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# Persistent TCP connection to Balatro server
balatro_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_to_proxy = False


def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    simulated_id = base + (t % 100000)
    return f"{simulated_id}.263"


def build_mod_hash(encrypt_id):
    return (
        f"theOrder=true;unlocked=true;encryptID={encrypt_id};"
        f"serversideConnectionID=423bca98;FantomsPreview=2.3.0;"
        f"Multiplayer={VERSION};Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;TheOrder-MultiplayerIntegration"
    )


def send_keepalive():
    while True:
        try:
            balatro_socket.sendall(b"action:keepAliveAck\n")
            print("[✓] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break


def handle_relay(proxy_ws):
    try:
        while True:
            data = balatro_socket.recv(4096)
            if not data:
                break
            asyncio.run(proxy_ws.send(data))
    except Exception as e:
        print(f"[X] Relay error (Balatro → Proxy): {e}")


async def proxy_handler(websocket):
    global connected_to_proxy
    print("[Relay] Proxy connected via WebSocket")
    connected_to_proxy = True

    try:
        while True:
            data = await websocket.recv()
            print(f"[Proxy → Balatro] {data!r}")
            balatro_socket.sendall(data)
    except Exception as e:
        print(f"[X] WebSocket receive error: {e}")
    finally:
        connected_to_proxy = False
        print("[Relay] Proxy disconnected")


async def main():
    print("[Relay] Relay bot starting...")
    print(f"[Relay] Connecting to Balatro server at {BALATRO_HOST}:{BALATRO_PORT}...")
    balatro_socket.connect((BALATRO_HOST, BALATRO_PORT))
    print("[Relay] Connected to Balatro server.")

    encrypt_id = generate_encrypt_id()
    mod_hash = build_mod_hash(encrypt_id)

    print(f"[Relay] encryptID = {encrypt_id}")
    print("[Relay] Sending handshake...")
    balatro_socket.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
    balatro_socket.sendall(f"action:version,version:{VERSION}\n".encode())
    balatro_socket.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
    print("[Relay] Handshake sent.")

    threading.Thread(target=send_keepalive, daemon=True).start()
    threading.Thread(target=handle_relay, args=(None,), daemon=True).start()

    print(f"[Relay] Listening for proxy on port {RELAY_PORT}...")
    async with websockets.serve(proxy_handler, host="0.0.0.0", port=RELAY_PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
