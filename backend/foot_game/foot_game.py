from fastapi.websockets import WebSocket, WebSocketState
from pydantic import BaseModel, ConfigDict

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
    ws: WebSocket

class Block(BaseModel):
    owner: Optional[Player] = None
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
            self.map[player.pos_x][player.pos_y].owner = player
            if self.now_player is None:
                self.now_player = player
        
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
        await self.broadcast({
            "type": "INFO",
            "data": f"{player.user.display_name} 移動完成。"
        })

        if target_block.owner is None:
            target_block.owner = player
            target_block.has_bomb = bomb
        else:
            ox, oy = target_block.owner.pos_x, target_block.owner.pos_y
            if ox == target_x and oy == target_y:
                target_block.owner.live = False
                await self.broadcast({
                    "type": "ERROR",
                    "data": f"{target_block.owner.user.display_name} 被 {player.user.display_name} 踩死了。"
                })
                target_block.owner = player
                target_block.has_bomb = bomb
            elif target_block.has_bomb:
                player.live = False
                target_block.has_bomb = False
                await self.broadcast({
                    "type": "ERROR",
                    "data": f"{player.user.display_name} 被 {target_block.owner.user.display_name} 炸死了。"
                })
            else:
                await player.ws.send_json({
                    "type": "WARNING",
                    "data": f"你踩到 {target_block.owner.user.display_name} 的足跡了。"
                })
                await target_block.owner.ws.send_json({
                    "type": "WARNING",
                    "data": f"你的足跡被 {player.user.display_name} 踩到了。"
                })
                target_block.owner = player
                target_block.has_bomb = bomb
        
        await self.next_round()
            
        
    def generate_map(self, player: Player):
        def dump_block(block: Block):
            data = {
                "owner": None if block.owner is None else block.owner.model_dump(exclude=["ws"]),
                "has_bomb": block.has_bomb
            }
            return data
        if player.observer or not player.live or self.end:
            return list(map(lambda line: list(map(dump_block, line)), self.map))
        return list(map(
            lambda line: list(map(
                lambda b: dump_block(b) if b.owner == player else dump_block(Block()),
                line
            )),
            self.map
        ))

    def check_around(self, player: Player) -> bool:
        if player.observer or not player.live:
            return False
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0: continue
                tx: int = player.pos_x + dx
                ty: int = player.pos_y + dy
                if tx < 0 or tx >= len(self.map): continue
                if ty < 0 or ty >= len(self.map[0]): continue
                target_block = self.map[tx][ty]
                if target_block.owner is None: continue
                if target_block.owner != player:
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