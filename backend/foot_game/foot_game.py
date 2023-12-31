from fastapi.websockets import WebSocket, WebSocketState
from pydantic import BaseModel, ConfigDict

from random import choice
from typing import Optional

from schemas.user import User

class Player(BaseModel):
    model_config=ConfigDict(arbitrary_types_allowed=True)
    user: User
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    bomb_count: Optional[int] = None
    observer: bool = False
    live: bool = True
    count: int = 0
    ws: WebSocket

class Block(BaseModel):
    owners: list[Player] = []
    has_bomb: bool = False

class FootGame():
    end: bool = False
    map: list[list[Block]] = []
    now_player: Optional[Player] = None
    players: list[Player] = []

    def __init__(
        self,
        width: int,
        height: int,
        bomb_count: int,
        start_position: list[tuple[int, int]],
        players: list[Player]
    ) -> None:
        self.map = list([])
        self.now_player = None
        self.players = list([])
        self.end = False
        for _ in range(width):
            self.map.append([])
            for _ in range(height):
                self.map[-1].append(Block())
        for i, player in enumerate(filter(lambda player: not player.observer, players)):
            player.bomb_count = bomb_count
            player.pos_x, player.pos_y = start_position[i]
            self.map[player.pos_x][player.pos_y].owners = [player]
            player.count = 1
        self.now_player = choice(list(filter(lambda player: not player.observer, players)))
        
        self.players = players
    
    async def broadcast(self, data):
        for player in self.players:
            try:
                await player.ws.send_json(data)
            except: pass
    
    async def exit(self, player: Player):
        live_players: list[Player] = list(filter(lambda player: player.live and not player.observer, self.players))
        if player == self.now_player and not self.end:
            now_index = live_players.index(player)
            self.now_player = live_players[(now_index + 1) % len(live_players)]
            self.players.remove(player)
            await self.next_round(False)
        else:
            self.players.remove(player)
            if (len(live_players) <= 2):
                await self.next_round(False)
        player.live = False


    async def move(self, player: Player, target_x: int, target_y: int, bomb: bool):
        if self.end: return
        if self.now_player != player:
            await player.ws.send_json({
                "type": "ERROR",
                "data": "當前不是你的回合。"
            })
            return
        elif abs(target_x - player.pos_x) + abs(target_y - player.pos_y) != 1:
            await player.ws.send_json({
                "type": "ERROR",
                "data": "無法移動至該處。"
            })
            return
        elif target_x < 0 or target_x >= len(self.map) or target_y < 0 or target_y >= len(self.map[0]):
            await player.ws.send_json({
                "type": "ERROR",
                "data": "無法移動至該處。"
            })
            return
        elif bomb:
            if player.bomb_count == 0:
                await player.ws.send_json({
                    "type": "ERROR",
                    "data": "地雷不足。"
                })
                return
            player.bomb_count -= 1
        
        target_block = self.map[target_x][target_y]
        player.pos_x = target_x
        player.pos_y = target_y
        player.count += 1
        await self.broadcast({
            "type": "INFO",
            "data": f"{player.user.display_name} 移動完成。 第 {player.count} 個 {player.user.display_name} 出現了。"
        })

        if len(target_block.owners) == 0:
            target_block.owners.append(player)
            target_block.has_bomb = bomb
        else:
            for owner in target_block.owners:
                ox, oy = owner.pos_x, owner.pos_y
                if ox == target_x and oy == target_y:
                    owner.live = False
                    await self.broadcast({
                        "type": "ERROR",
                        "data": f"{owner.user.display_name} 被 {player.user.display_name} 踩死了。"
                    })
                    target_block.owners = [player]
                    target_block.has_bomb = bomb
                    break
                elif target_block.has_bomb:
                    player.live = False
                    target_block.has_bomb = False
                    await self.broadcast({
                        "type": "ERROR",
                        "data": f"{player.user.display_name} 被 {owner.user.display_name} 炸死了。"
                    })
                    break
                else:
                    await player.ws.send_json({
                        "type": "WARNING",
                        "data": f"你踩到 {owner.user.display_name} 的足跡了。"
                    })
                    await owner.ws.send_json({
                        "type": "WARNING",
                        "data": f"你的足跡被 {player.user.display_name} 踩到了。"
                    })
                    target_block.owners.append(player)
                    target_block.has_bomb = bomb
                    break
        
        await self.next_round()
            
        
    def generate_map(self, player: Player):
        def dump_block(block: Block, player: Optional[Player] = None):
            if player is None:
                data = {
                    "owner": None if len(block.owners) == 0 else block.owners[-1].model_dump(exclude=["ws"]),
                    "has_bomb": block.has_bomb
                }
            else:
                data = {
                    "owner": None if player not in block.owners else player.model_dump(exclude=["ws"]),
                    "has_bomb": block.has_bomb
                }
            return data
        
        if player.observer or not player.live or self.end:
            return list(map(lambda line: list(map(dump_block, line)), self.map))
        
        return list(map(
            lambda line: list(map(
                lambda b: dump_block(b, player),
                line
            )),
            self.map
        ))

    def check_around(self, player: Player) -> bool:
        if player.observer or not player.live:
            return False
        for other in self.players:
            if other == player: continue
            if abs(other.pos_x - player.pos_x) == 1:
                return True
            if abs(other.pos_y - player.pos_y) == 1:
                return True
        return False

    async def next_round(self, update: bool = True):
        players: list[Player] = list(filter(lambda player: not player.observer, self.players))
        live_players: list[Player] = list(filter(lambda player: player.live, players))
        if len(live_players) > 1:
            if update:
                now_player_index = players.index(self.now_player) + 1
                while not players[now_player_index % len(players)].live:
                    now_player_index += 1
                self.now_player = players[now_player_index % len(players)]
            await self.now_player.ws.send_json({
                "type": "INFO",
                "data": "輪到你了。"
            })
        else:
            self.end = True
            try:
                self.now_player = live_players[0]
            except: pass

        await self.send_update()
    
    async def send_update(self):
        for player in self.players:
            try:
                await player.ws.send_json({
                    "type": "DATA",
                    "data": {
                        "map": self.generate_map(player),
                        "current_player": self.now_player.user.id,
                        "around": self.check_around(player),
                        "player": player.model_dump(exclude=["ws"])
                    }
                })
            except: pass
        if self.end:
            await self.broadcast({
                "type": "END",
                "data": f"遊戲結束，獲勝的是 {self.now_player.user.display_name}。"
            })