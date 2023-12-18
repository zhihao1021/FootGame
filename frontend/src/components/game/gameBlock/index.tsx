import {
    ChangeEvent,
    ReactElement, useState,
} from "react";

import { GameData, GameUserData } from "../../../schemas/game";

import "./index.scss";

type propsType = Readonly<{
    ws: WebSocket,
    gameData: GameData,
    gameUserData: GameUserData,
    scrollPage: (page: number) => void,
}>;

export default function GameBlock(props: propsType): ReactElement {
    const {
        ws,
        gameData,
        gameUserData,
        scrollPage,
    } = props;
    const [bombState, setBombState] = useState<boolean>(false);

    return (
        <div className="gameBlock">
            <h3>Game</h3>
            <div className="buttonBar">
                <div className="bombCount">剩餘地雷: {gameData.player.bomb_count}</div>
                <label>
                    使用地雷
                    <input type="checkbox" checked={bombState} onChange={(event: ChangeEvent<HTMLInputElement>) => {
                        if (gameData.player.bomb_count > 0) {
                            setBombState(event.target.checked)
                        }
                        else setBombState(false);
                    }} />
                </label>
                <div className="around" data-show={gameData.around}>周圍出現足跡</div>
            </div>
            <div className="gameBoard">
                {
                    gameData.map.map((data, x) => (
                        <div key={x}>
                            {data.map((block, y) => (
                                <div
                                    key={y}
                                    className="block"
                                    data-bomb={block.has_bomb}
                                    data-now={gameData.player.pos_x === x && gameData.player.pos_y === y}
                                    onClick={() => {
                                        ws.send(JSON.stringify({
                                            type: "MOVE",
                                            data: {
                                                x: x,
                                                y: y,
                                                bomb: bombState
                                            }
                                        }));
                                        setBombState(false);
                                    }}
                                >
                                    { block.owner ? <img alt="block" src={block.owner.user.avatar_url} /> : undefined }
                                </div>
                            ))}
                        </div>
                    ))
                }
            </div>
            <button className="pageButton" onClick={() => { scrollPage(1); }}>Next</button>
        </div>
    );
}
