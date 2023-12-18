from pydantic import BaseModel

from typing import Coroutine


class PlayerData(BaseModel):
    live: bool
    bomb_count: int
    player_id: int
    position: tuple[int, int]
    observer: bool


class NextRoundData(BaseModel):
    round: int
    your_round: bool
    round_player: int
    dead_player: list[int]
    map_data: list[list[int]]
    around: bool
    step: bool
    player: PlayerData


class FootGame:
    width: int
    height: int
    start_point: list[tuple[int, int]]
    data: list[list[int]] = []
    joined_player_id: int = 0
    game_round: int = 0
    now_player: int = 0
    player_list: list["Player"] = []
    started: bool = False

    def __init__(
        self,
        width: int,
        height: int,
        start_point: list[tuple[int, int]],
    ):
        self.width = width
        self.height = height
        self.start_point = start_point

        for _ in range(self.width):
            self.data.append([0] * self.height)

    def join(self, player: "Player") -> tuple[int, tuple[int, int]]:
        player_id = self.joined_player_id
        if player_id >= len(self.start_point) or player.observer:
            return -1, -1, -1
        self.joined_player_id += 1
        self.player_list.append(player)
        return player_id, self.start_point[player_id]

    def gen_map_data(self, player: "Player") -> list[list[bool]]:
        player_id = player.player_id
        map_data: list[list[bool]] = []
        for i in range(self.width):
            map_data.append([])
            for j in range(self.height):
                data = self.data[i][j]
                if not player.live:
                    map_data[i].append(data)
                    continue
                map_data[i].append(data & (1 << (2 * player_id)))
        return map_data

    def check_around(self, player: "Player") -> bool:
        player_id = player.player_id
        pos_x, pos_y = player.position
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                mask = (1 << (2 * len(self.player_list))) - 1
                mask ^= 0b11 << (2 * player_id)
                if self.data[pos_x + dx][pos_y + dy] & mask != 0:
                    return True
        return False

    async def start(self):
        self.game_round += 1
        self.started = True
        dead_player = list(filter(lambda p: not p.live, self.player_list))
        for player in self.player_list:
            await player.next_callback(NextRoundData(
                round=self.game_round,
                your_round=self.now_player == player.player_id,
                round_player=self.now_player,
                dead_player=dead_player,
                map_data=self.gen_map_data(player),
                around=self.check_around(player),
                step=False,
                player=player.data
            ))

    async def move(self, player: "Player", target_x: int, target_y: int, bomb: bool) -> bool:
        if not self.started:
            return False
        player_id = player.player_id
        player_x, player_y = player.position
        if abs(player_x - target_x) + abs(player_y - target_y) != 1:
            return False
        if target_x < 0 or target_x >= self.width:
            return False
        if target_y < 0 or target_y >= self.height:
            return False
        target = self.data[target_x][target_y]
        if (target >> (2 * player_id)) & 1 != 0:
            return False
        step = False
        around = self.check_around(player)
        if around:
            for i in range(len(self.player_list)):
                target >>= 2 * i
                if 0b10 & target != 0:
                    player.live = False
                    self.data[target_x][target_y] ^= 0b10 << i
                    break
                if 0b01 & target != 0:
                    player = self.player_list[i]
                    if player.live:
                        step = True
                        player.live = False
                    break

        self.data[target_x][target_y] |= 1 << (2 * player_id)
        if bomb:
            self.data[target_x][target_y] |= 0b10 << (2 * player_id)
        player.position = (target_x, target_y)

        self.now_player += 1
        self.now_player %= len(self.player_list)
        while not self.player_list[self.now_player].live:
            self.now_player += 1
            self.now_player %= len(self.player_list)

        self.game_round += 1
        dead_player = list(filter(lambda p: not p.live, self.player_list))
        for player in self.player_list:
            await player.next_callback(NextRoundData(
                round=self.game_round,
                your_round=self.now_player == player.player_id,
                round_player=self.now_player,
                dead_player=dead_player,
                map_data=self.gen_map_data(player),
                around=self.check_around(player),
                step=step if player.player_id == player_id else False,
                player=player.data
            ))

        return True


class Player:
    game: FootGame
    live: bool = True
    bomb_count: int
    player_id: int
    position: tuple[int, int]
    next_callback: Coroutine[None, NextRoundData, None]
    observer: bool

    @property
    def data(self) -> PlayerData:
        return PlayerData(
            live=self.live,
            bomb_count=self.bomb_count,
            player_id=self.player_id,
            position=self.position,
            observer=self.observer
        )

    def __init__(
        self,
        game: FootGame,
        bomb_count: int,
        next_callback: Coroutine,
        observer: bool = False
    ):
        self.game = game
        self.observer = observer
        self.bomb_count = bomb_count
        self.player_id, self.position = game.join(self)
        self.next_callback = next_callback
        if observer:
            self.live = False

    def check_your_round(self) -> bool:
        return self.player_id == self.game.now_player and self.live

    async def move(self, pos_x: int, pos_y: int, bomb: bool) -> bool:
        if not self.check_your_round() or not self.live:
            return False
        if bomb:
            if self.bomb_count == 0:
                return False
            self.bomb_count -= 1
        return await self.game.move(self, pos_x, pos_y, bomb)
