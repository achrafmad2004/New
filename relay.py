# relay.py
import asyncio
import websockets
import socket
import traceback

BALATRO_HOST = "161.35.252.15"
BALATRO_PORT = 8788
DEBUG = True

def log(prefix, msg):
    print(f"[{prefix}] {msg}")

async def handle_connection(websocket):
    log("+", f"Proxy connected via WebSocket")
    try:
        reader, writer = await asyncio.open_connection(BALATRO_HOST, BALATRO_PORT)
        log("+", f"Connected to Balatro server at {BALATRO_HOST}:{BALATRO_PORT}")

        async def tcp_to_ws():
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        log("-", "Balatro server closed connection")
                        break
                    if DEBUG:
                        log("→", f"Server → Proxy: {len(data)} bytes")
                    await websocket.send(data)
            except Exception as e:
                log("X", f"Error [Server → Proxy]: {e}")
                traceback.print_exc()

        async def ws_to_tcp():
            try:
                async for message in websocket:
                    if DEBUG:
                        log("←", f"Proxy → Server: {len(message)} bytes")
                    writer.write(message)
                    await writer.drain()
            except Exception as e:
                log("X", f"Error [Proxy → Server]: {e}")
                traceback.print_exc()

        await asyncio.gather(tcp_to_ws(), ws_to_tcp())

    except Exception as e:
        log("X", f"Relay handler error: {e}")
        traceback.print_exc()

async def main():
    log("*", "Relay listening on :20001")
    async with websockets.serve(handle_connection, "0.0.0.0", 20001, max_size=None):
        await asyncio.Future()

asyncio.run(main())
