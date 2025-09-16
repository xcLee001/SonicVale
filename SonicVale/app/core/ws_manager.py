# ws_manager.py
from fastapi import WebSocket
from typing import List

class WSManager:
    def __init__(self):
        self.conns: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.conns.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.conns:
            self.conns.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.conns:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for d in dead:
            self.disconnect(d)

manager = WSManager()
