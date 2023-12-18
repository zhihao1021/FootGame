import UserData from "../contexts/user"
import JWTData from "./jwt"

export interface Player {
    user: JWTData,
    pos_x: number,
    pos_y: number,
    bomb_count: number,
    observer: boolean,
    live: boolean,
}

export interface Block {
    owner: Player|null,
    has_bomb: boolean
}

export interface GameData {
    map: Array<Array<Block>>,
    current_player: number,
    around: boolean,
    player: Player
};

export interface GameUserData {
    host: number,
    users: Array<JWTData>
};
