import asyncio
import websockets
import json

async def test():
    # Use 127.0.0.1 to avoid Windows localhost IPv6 resolution issues
    uri = 'ws://127.0.0.1:8000/ws'
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        print('CONNECTED!')
        print("Sending handshake 'hello'...")
        await ws.send('hello')
        response = await ws.recv()
        print(f"Received: {response}")

asyncio.run(test())
