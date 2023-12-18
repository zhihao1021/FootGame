from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from os import urandom
from typing import Optional, Union

from foot_game import FootGame, Player
from schemas.user import User

from ..validator import get_user


class GameSetting(BaseModel):
    width: int
    height: int
    bomb_count: int
    start_position: list[tuple[int, int]]


class RoomManger():
    game: Optional[FootGame] = None
    host: Player
    players: list[Player] = []
    setting: GameSetting

    def __init__(self, user: User, ws: WebSocket, setting: GameSetting) -> None:
        player = Player(
            user=user,
            ws=ws,
        )
        self.game = None
        self.players = list([])
        self.host = player
        self.players.append(player)
        self.setting = setting

    async def broadcast(self, data):
        for player in self.players:
            # try:
                await player.ws.send_json(data)
            # except RuntimeError: pass

    async def update_user(self):
        await self.broadcast({
            "type": "USER",
            "data": {
                "host": self.host.user.id,
                "users": list(map(lambda player: player.user.model_dump(), self.players)),
            }
        })

    async def start(self, player: Player):
        if self.host == player:
            if self.game is not None:
                await player.ws.send_json({
                    "type": "WARNING",
                    "data": "遊戲已經開始了。"
                })
                return
            if len(self.players) < 2:
                await player.ws.send_json({
                    "type": "WARNING",
                    "data": "房間人數不足。"
                })
                return
            self.game = FootGame(
                **self.setting.model_dump(), players=self.players)
            await player.ws.send_json({
                "type": "INFO",
                "data": "遊戲開始。"
            })
            await self.game.next_round()
        else:
            await player.ws.send_json({
                "type": "WARNING",
                "data": "你不是房主。"
            })

    async def join(self, user: User, ws: WebSocket) -> Optional[Player]:
        if self.game is not None:
            await ws.send_json({
                "type": "REJECT",
                "data": "遊戲已經開始了。"
            })
            return
        elif user.id in filter(lambda player: player.user.id, self.players):
            await ws.send_json({
                "type": "REJECT",
                "data": "你已經在遊戲裡了。"
            })
            return
        else:
            player = Player(
                user=user,
                ws=ws
            )
            if len(list(filter(lambda player: not player.observer, self.players))) >= len(self.setting.start_position):
                player.observer = True
                player.live = False
            self.players.append(player)
            await self.broadcast({
                "type": "INFO",
                "data": f"{user.display_name} 加入遊戲。"
            })
            await self.update_user()
            return player

    async def exit(self, player: Player):
        if self.game is None:
            self.players.remove(player)
        else:
            await self.game.exit(player)

        if self.host == player and len(self.players) > 0:
            self.host = self.players[0]
        elif len(self.players) == 0:
            self.host = None

        if len(self.players) == 0:
            return

        await self.broadcast({
            "type": "WARNING",
            "data": f"{player.user.display_name} 離開遊戲。"
        })
        await self.update_user()


router = APIRouter(
    prefix="/game",
    tags=["Game"]
)
room_data: dict[str, Union[RoomManger, GameSetting]] = {}


@router.post("")
async def create_game(data: GameSetting):
    key = urandom(32).hex()
    room_data[key] = data
    return key


@router.websocket("/ws/{room_id}")
async def game_room(room_id: str, ws: WebSocket):
    await ws.accept()
    token = await ws.receive_text()
    user = get_user(token)

    room = room_data.get(room_id, GameSetting(
        width=3, height=12, bomb_count=3, start_position=[[1, 0], [1, 11]]))
    if room is None:
        await ws.send_json({
            "type": "REJECT",
            "data": "房間不存在。"
        })
        return

    if type(room) == GameSetting:
        room = RoomManger(user=user, ws=ws, setting=room)
        room_data[room_id] = room
        await room.update_user()
        player = room.players[-1]
    elif type(room) == RoomManger:
        player = await room.join(user, ws)
        if player is None:
            return
    else:
        return

    try:
        while True:
            try:
                data = await ws.receive_json()
                if data["type"] == "START":
                    await room.start(player)
                elif data["type"] == "MOVE":
                    if room.game is None:
                        await ws.send_json({
                            "type": "WARNING",
                            "data": "遊戲尚未開始。"
                        })
                        continue
                    await room.game.move(
                        player,
                        target_x=data["data"]["x"],
                        target_y=data["data"]["y"],
                        bomb=data["data"]["bomb"]
                    )
            except WebSocketDisconnect as e: raise e
            except: pass
    except WebSocketDisconnect:
        await room.exit(player)
        if room.host is None or len(room.players) == 0:
            del room_data[room_id]
