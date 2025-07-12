import asyncio
import websockets
import socket
import threading
import time

# === CONFIG ===
BALATRO_HOST = "161.35.252.15"
BALATRO_PORT = 8788
RELAY_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# === CONNECTION TO BALATRO SERVER (TCP) ===
def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    simulated_id = base + (t % 100000)
    return f"{simulated_id}.263"

def build_mod_hash(encrypt_id):
    return (
        f"theOrder=true;"
        f"unlocked=true;"
        f"encryptID={encrypt_id};"
        f"serversideConnectionID=423bca98;"
        f"FantomsPreview=2.3.0;"
        f"Multiplayer={VERSION};"
        f"Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;"
        f"TheOrder-MultiplayerIntegration"
    )

def connect_to_balatro():
    print("[Relay] Connecting to Balatro server...")
    sock = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
    encrypt_id = generate_encrypt_id()
    mod_hash = build_mod_hash(encrypt_id)

    sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
    sock.sendall(f"action:version,version:{VERSION}\n".encode())
    sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
    print(f"[Relay] Handshake complete. encryptID={encrypt_id}")

    def keep_alive_loop():
        while True:
            try:
                sock.sendall(b"action:keepAliveAck\n")
                print("[✓] Sent keepAliveAck")
                time.sleep(4)
            except Exception as e:
                print(f"[Relay] Keep-alive failed: {e}")
                break

    threading.Thread(target=keep_alive_loop, daemon=True).start()
    return sock

balatro_sock = connect_to_balatro()

# === RELAY HANDLER (WebSocket <-> TCP) ===
async def relay_handler(websocket):
    print("[Relay] Proxy connected.")
    try:
        async def recv_ws_and_send_tcp():
            while True:
                data = await websocket.recv()
                print(f"[WS → TCP] {data[:100]!r}")
                balatro_sock.sendall(data.encode())

        def recv_tcp_and_send_ws():
            try:
                while True:
                    data = balatro_sock.recv(4096)
                    if not data:
                        break
                    print(f"[TCP → WS] {data[:100]!r}")
                    asyncio.run(websocket.send(data.decode()))
            except Exception as e:
                print(f"[Relay] TCP → WS error: {e}")

        threading.Thread(target=recv_tcp_and_send_ws, daemon=True).start()
        await recv_ws_and_send_tcp()

    except Exception as e:
        print(f"[Relay] Proxy connection failed: {e}")

# === START SERVER ===
async def main():
    print(f"[Relay] Listening on port {RELAY_PORT} (WebSocket)...")
    async with websockets.serve(relay_handler, "0.0.0.0", RELAY_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
