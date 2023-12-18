from fastapi import WebSocket

from .foot_game.foot_game import FootGame, Player

class GameRoom:
    connections: list[WebSocket]
    def  __init__(self, creater: WebSocket) -> None:
        self.connections = [creater]

    def add_websocket(self, websocket: WebSocket) -> Player:
        self.connections.append(websocket)

    async def broadcast_json(self, data: dict):
        for websocket in self.connections:
            await websocket.send_json(data)
