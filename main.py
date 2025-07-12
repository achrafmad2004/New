import asyncio
from aiohttp import web

BALATRO_HOST = "balatro.virtualized.dev"
BALATRO_PORT = 8788

class BalatroSession:
    def __init__(self):
        self.reader = None
        self.writer = None
        self.client_ws = None  # WebSocket from the proxy

    async def connect(self):
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

balatro_session = BalatroSession()

async def start_background_tasks(app):
    await balatro_session.connect()
    app['balatro_task'] = asyncio.create_task(balatro_session.read_from_balatro())

app = web.Application()
app.router.add_get('/ws', balatro_session.handle_client)
app.on_startup.append(start_background_tasks)

web.run_app(app, port=8000)
