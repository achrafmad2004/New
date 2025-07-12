### Directory: balatro-relay-persistent

# ================================
# File: relay.py (Railway - Cloud)
# ================================

import socket
import threading
import time

SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001

USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

sessions = {}


def generate_encrypt_id():
    base = 45385400000
    t = int(time.time() * 1000)
    return f"{base + (t % 100000)}.263"


def build_mod_hash(eid):
    return (
        f"theOrder=true;unlocked=true;encryptID={eid};serversideConnectionID=423bca98;"
        f"FantomsPreview=2.3.0;Multiplayer={VERSION};Saturn=0.2.2-E-ALPHA;"
        f"Steamodded-1.0.0~BETA-0614a;TheOrder-MultiplayerIntegration"
    )


def send_keep_alive_loop(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[KA] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break


def handle_proxy(proxy_sock, balatro_sock):
    def forward(src, dst, label):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                print(f"[{label}] {data}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Forwarding error ({label}): {e}")
        finally:
            print(f"[~] Closed {label}")
            src.close()
            dst.close()

    threading.Thread(target=forward, args=(proxy_sock, balatro_sock, "Proxy → Server")).start()
    threading.Thread(target=forward, args=(balatro_sock, proxy_sock, "Server → Proxy")).start()


def main():
    print("[Relay] Relay bot starting...")

    try:
        print(f"[Relay] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        balatro_sock = socket.create_connection((SERVER_HOST, SERVER_PORT))
        print("[Relay] Connected to Balatro server")

        eid = generate_encrypt_id()
        mod_hash = build_mod_hash(eid)

        print(f"[Relay] encryptID = {eid}")
        print("[Relay] Sending handshake to Balatro")
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        balatro_sock.sendall(f"action:version,version:{VERSION}\n".encode())
        balatro_sock.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[Relay] Handshake sent")

        threading.Thread(target=send_keep_alive_loop, args=(balatro_sock,), daemon=True).start()

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("0.0.0.0", RELAY_PORT))
        listener.listen(1)
        print(f"[Relay] Listening for proxy on port {RELAY_PORT}...")

        while True:
            proxy_sock, addr = listener.accept()
            print(f"[Relay] Proxy connected from {addr}")
            handle_proxy(proxy_sock, balatro_sock)

    except Exception as e:
        print(f"[Relay] Error: {e}")


if __name__ == "__main__":
    main()


# =====================================
# File: requirements.txt (for Railway)
# =====================================

# Nothing required beyond stdlib, but Railway expects this file


# ========================
# File: railway.json
# ========================
{
  "build": {
    "env": {
      "PYTHONUNBUFFERED": "1"
    }
  },
  "services": {
    "relay": {
      "port": 20001,
      "protocol": "tcp"
    }
  }
}


# ========================
# File: README.md
# ========================

# Balatro Persistent Relay (Railway)

This repository hosts a Railway-compatible TCP relay that maintains a persistent connection to the Balatro multiplayer server, even when the proxy (on your local PC) disconnects temporarily.

## Features
- Persistent TCP connection to Balatro server
- Waits for reconnecting proxy
- Sends regular keep-alive ACKs
- Logs traffic to and from the Balatro server

## Usage

1. Deploy this repo to [Railway](https://railway.app/)
2. Set TCP service port to `20001`
3. Point your proxy (on your PC) to `your-app-name.proxy.rlwy.net:20001`
4. Run Balatro through the proxy

## Files
- `relay.py`: the cloud relay logic
- `requirements.txt`: empty, just for compatibility
- `railway.json`: configures TCP port for Railway

---

You can now add the local files separately:
- `proxy.py` and `launcher.py` will stay **on your PC only**.
