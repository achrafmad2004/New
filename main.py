import asyncio
from aiohttp import web

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788

class BalatroSession:
    def __init__(self):
        self.reader = None
        self.writer = None
        self.client_ws = None

    async def connect_to_balatro(self):
        self.reader, self.writer = await asyncio.open_connection(BALATRO_HOST, BALATRO_PORT)
        print("[Relay] Connected to Balatro server")

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
        print("[Relay] Proxy connected")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.BINARY:
                    self.writer.write(msg.data)
                    await self.writer.drain()
        except Exception as e:
            print("[Relay] WebSocket error:", e)
        finally:
            print("[Relay] Proxy disconnected")
            self.client_ws = None
        return ws

relay = BalatroSession()

async def startup(app):
    await relay.connect_to_balatro()
    app['relay_to_balatro'] = asyncio.create_task(relay.read_from_balatro())

app = web.Application()
app.router.add_get("/ws", relay.handle_client)
app.on_startup.append(startup)

web.run_app(app, port=8000)
