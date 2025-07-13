# relay.py
import socket
import threading
import asyncio
import websockets
import traceback

BALATRO_HOST = "161.35.252.15"
BALATRO_PORT = 8788
DEBUG = True

def log(prefix, msg):
    print(f"[{prefix}] {msg}")

def forward_tcp_to_ws(tcp_sock, websocket):
    try:
        while True:
            data = tcp_sock.recv(4096)
            if not data:
                log("-", "Balatro server closed connection")
                break
            if DEBUG:
                log("→", f"To Proxy: {len(data)} bytes")
            asyncio.run(websocket.send(data))
    except Exception as e:
        log("X", f"Error TCP→WS: {e}")
        traceback.print_exc()
    finally:
        asyncio.run(websocket.close())
        tcp_sock.close()

async def forward_ws_to_tcp(websocket, tcp_sock):
    try:
        async for data in websocket:
            if DEBUG:
                log("←", f"To Server: {len(data)} bytes")
            tcp_sock.sendall(data)
    except Exception as e:
        log("X", f"Error WS→TCP: {e}")
        traceback.print_exc()
    finally:
        tcp_sock.close()

async def handler(websocket, path):
    log("+", "Proxy connected via WebSocket")
    try:
        tcp_sock = socket.create_connection((BALATRO_HOST, BALATRO_PORT))
        log("+", f"Connected to Balatro server at {BALATRO_HOST}:{BALATRO_PORT}")
        threading.Thread(target=forward_tcp_to_ws, args=(tcp_sock, websocket), daemon=True).start()
        await forward_ws_to_tcp(websocket, tcp_sock)

    except Exception as e:
        log("X", f"Relay handler error: {e}")
        traceback.print_exc()

async def main():
    log("*", "Relay listening on :20001")
    async with websockets.serve(handler, "0.0.0.0", 20001, max_size=None):
        await asyncio.Future()  # run forever

asyncio.run(main())
