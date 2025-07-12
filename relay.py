# === relay.py (Railway-hosted, persistent TCP to server + WebSocket to proxy) ===

import asyncio
import websockets
import socket
import threading
import time

# Config
BALATRO_SERVER = ("161.35.252.15", 8788)
RELAY_WS_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# TCP connection to Balatro server
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    simulated_id = base + (t % 100000)
    return f"{simulated_id}.263"

def build_mod_hash(encrypt_id):
    return (
        f"theOrder=true;unlocked=true;encryptID={encrypt_id};serversideConnectionID=423bca98;"
        f"FantomsPreview=2.3.0;Multiplayer={VERSION};Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;TheOrder-MultiplayerIntegration"
    )

def start_keep_alive():
    while True:
        try:
            server_sock.sendall(b"action:keepAliveAck\n")
            print("[✓] Sent keepAliveAck")
            time.sleep(4)
        except:
            break

def forward(src, dst, label):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            print(f"[{label}] {data!r}")
            dst.sendall(data)
    except Exception as e:
        print(f"[X] Relay error ({label}): {e}")

def handle_ws_messages(websocket):
    try:
        while True:
            data = websocket.recv()
            if data:
                server_sock.sendall(data.encode())
    except Exception as e:
        print(f"[X] WS receive error: {e}")

async def handle_proxy(websocket):
    print("[Relay] Proxy connected via WebSocket.")

    def relay_to_proxy():
        try:
            while True:
                data = server_sock.recv(4096)
                if not data:
                    break
                asyncio.run(websocket.send(data.decode(errors='ignore')))
        except Exception as e:
            print(f"[X] Server → Proxy error: {e}")

    threading.Thread(target=relay_to_proxy).start()

    try:
        async for message in websocket:
            server_sock.sendall(message.encode())
    except Exception as e:
        print(f"[X] Proxy → Server error: {e}")

async def main():
    print("[Relay] Connecting to Balatro server at {}:{}...".format(*BALATRO_SERVER))
    server_sock.connect(BALATRO_SERVER)
    print("[Relay] Connected to Balatro server.")

    encrypt_id = generate_encrypt_id()
    mod_hash = build_mod_hash(encrypt_id)

    print("[Relay] encryptID =", encrypt_id)
    print("[Relay] Sending handshake...")
    server_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
    server_sock.sendall(f"action:version,version:{VERSION}\n".encode())
    server_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
    print("[Relay] Handshake sent.")

    threading.Thread(target=start_keep_alive, daemon=True).start()

    print(f"[Relay] Listening for proxy WebSocket on :{RELAY_WS_PORT}...")
    async with websockets.serve(handle_proxy, "0.0.0.0", RELAY_WS_PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
