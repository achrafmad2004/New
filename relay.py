import socket
import threading
import time

# === CONFIG ===
SERVER_HOST = "161.35.252.15"
SERVER_PORT = 8788
RELAY_PORT = 20001
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

# === HELPERS ===

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

def send_keep_alive_loop(sock):
    while True:
        try:
            sock.sendall(b"action:keepAliveAck\n")
            print("[✓] Sent keepAliveAck")
            time.sleep(4)
        except Exception as e:
            print(f"[X] Keep-alive error: {e}")
            break

def relay_handler(client_sock, server_sock):
    def forward(src, dst, label):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                print(f"[{label}] {data}")
                dst.sendall(data)
        except Exception as e:
            print(f"[X] Relay error ({label}): {e}")
        finally:
            try:
                src.close()
                dst.close()
            except:
                pass

    threading.Thread(target=forward, args=(client_sock, server_sock, "Proxy → Server")).start()
    threading.Thread(target=forward, args=(server_sock, client_sock, "Server → Proxy")).start()

# === MAIN ===

def main():
    print("[Relay] Relay bot starting...")
    try:
        print(f"[Relay] Connecting to Balatro server at {SERVER_HOST}:{SERVER_PORT}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        print("[Relay] Connected to Balatro server.")

        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        print(f"[Relay] encryptID = {encrypt_id}")
        print("[Relay] Sending handshake...")
        s.sendall(f"action:username,username:{USERNAME},modHash:\n".encode())
        s.sendall(f"action:version,version:{VERSION}\n".encode())
        s.sendall(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        print("[Relay] Handshake sent.")

        threading.Thread(target=send_keep_alive_loop, args=(s,), daemon=True).start()

        relay_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        relay_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        relay_sock.bind(("0.0.0.0", RELAY_PORT))
        relay_sock.listen(1)

        print(f"[Relay] Listening for proxy on port {RELAY_PORT}...")

        while True:
            client_sock, addr = relay_sock.accept()
            print(f"[Relay] Proxy connected from {addr}")
            relay_handler(client_sock, s)

    except Exception as e:
        print(f"[X] Relay error: {e}")

if __name__ == "__main__":
    main()

# This repository hosts a Railway-compatible TCP relay that maintains a persistent
# connection to the Balatro multiplayer server, even when the proxy (on your local PC)
# disconnects temporarily.
