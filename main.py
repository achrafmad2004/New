import asyncio
from aiohttp import web
import time

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788
USERNAME = "Achraf~1"
VERSION = "0.2.11-MULTIPLAYER"

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

class BalatroRelay:
    def __init__(self):
        self.reader = None
        self.writer = None
        self.client_ws = None

    async def connect_to_balatro(self):
        self.reader, self.writer = await asyncio.open_connection(BALATRO_HOST, BALATRO_PORT)
        print("[Relay] Connected to Balatro server")
        await self.send_handshake()
        asyncio.create_task(self.send_keep_alive())

    async def send_handshake(self):
        encrypt_id = generate_encrypt_id()
        mod_hash = build_mod_hash(encrypt_id)

        print(f"[Relay] encryptID = {encrypt_id}")
        print("[Relay] Sending handshake to Balatro")
        self.writer.write(f"action:username,username:{USERNAME},modHash:\n".encode())
        self.writer.write(f"action:version,version:{VERSION}\n".encode())
        self.writer.write(f"action:username,username:{USERNAME},modHash:{mod_hash}\n".encode())
        await self.writer.drain()
        print("[Relay] Handshake sent")

    async def send_keep_alive(self):
        try:
            while True:
                await asyncio.sleep(4)
                self.writer.write(b"action:keepAliveAck\n")
                await self.writer.drain()
                print("[Relay] Sent keepAliveAck")
        except Exception as e:
            print(f"[Relay] Keep-alive failed: {e}")

    async def read_from_balatro(self):
        try:
            while True:
                data = await self.reader.read(4096)
                if not data:
                    print("[Relay] Balatro server disconnected")
                    break
                if self.client_ws:
                    await self.client_ws.send_bytes(data)
        except Exception as e:
            print("[Relay] Error reading from Balatro:", e)

    async def handle_client(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.client_ws = ws
        print("[Relay] Proxy connected via WebSocket")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.BINARY:
                    print(f"[Relay] Received {len(msg.data)} bytes from proxy")
                    self.writer.write(msg.data)
                    await self.writer.drain()
        except Exception as e:
            print("[Relay] WebSocket error:", e)
        finally:
            print("[Relay] Proxy disconnected")
            self.client_ws = None
        return ws

relay = BalatroRelay()

async def startup(app):
    await relay.connect_to_balatro()
    app['balatro_reader'] = asyncio.create_task(relay.read_from_balatro())

app = web.Application()
app.router.add_get("/ws", relay.handle_client)
app.on_startup.append(startup)

web.run_app(app, port=8000)
