import asyncio
import aiohttp
from aiohttp import web
import websockets
import json

last_offer = None
clients = {}


async def websocket_handler(request):
    global last_offer
    global clients
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    client_id = None

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            print(f"Message received: {data}")
            if data['type'] == 'register':
                client_id = data['id']
                clients[client_id] = ws
                print(f"Registered: {client_id}")

                # Send stored offer to new viewers
                if client_id == 'viewer':
                    streamer_ws = clients.get('streamer')
                    if streamer_ws is not None:
                        await ws.send_json({
                            'type': 'offer',
                            'from': 'streamer',
                            'sdp': last_offer  # Need to store offers
                        })
            else:
                # Store last offer from streamer
                if data['type'] == 'offer':
                    last_offer = data['sdp']

                # Relay messages to other clients
                for target_id, target_ws in clients.items():
                    print(f"Relaying message from {data['from']} to {target_id}")
                    if target_id != data['from']:
                        print(f"Relaying {data['type']} to {target_id}")
                        await target_ws.send_json(data)
    return ws


async def index(request):
    return aiohttp.web.FileResponse('./index.html')

app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/', index)
app.router.add_static('/', path='./', name='static')

if __name__ == '__main__':
    web.run_app(app, port=8080)
