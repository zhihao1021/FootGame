import { ReactElement, createRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { GameData, GameUserData } from "../../../schemas/game";
import { Message } from "..";

import "./index.scss";

type propsType = Readonly<{
    gameData: GameData | undefined,
    gameUserData: GameUserData,
    messageArray: Array<Message>,
    scrollPage: (page: number) => void
}>;

export default function InfoBlock(props: propsType): ReactElement {
    const ref = createRef<HTMLDivElement>();
    const {
        gameData,
        gameUserData,
        messageArray,
        scrollPage,
    } = props;
    const setNavigate = useNavigate();

    useEffect(() => {
        const target = ref.current;
        if (target === null) return;
        target.scroll(0, target.scrollHeight);
    }, [ref, messageArray])

    return (
        <div className="infoBlock">
            <h3>Players</h3>
            <div className="box">
                {gameUserData.users.map((user, key) => (
                    <div key={key} title={user.display_name} data-activate={gameData?.current_player === user.id}>
                        <img alt="avatar" src={user.avatar_url} />
                        <div>{user.display_name}</div>
                    </div>
                ))}
            </div>
            <h3>Message</h3>
            <div ref={ref} className="box">
                {messageArray.map((data, key) => (
                    <div key={key} data-level={data.level}>
                        {data.context}
                    </div>
                ))}
            </div>
            <button className="exitButton" onClick={() => { setNavigate("/"); }}>退出遊戲</button>
            <button className="pageButton" onClick={() => { scrollPage(0); }}>Back</button>
        </div>
    );
}
