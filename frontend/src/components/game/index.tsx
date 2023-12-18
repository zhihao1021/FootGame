import {
    Dispatch,
    ReactElement,
    SetStateAction,
    createRef,
    useEffect,
    useState,
    useContext,
} from "react";
import {
    useSearchParams,
    useNavigate,
} from "react-router-dom";

import InfoBlock from "./infoBlock";
import GameBlock from "./gameBlock";

import {
    GameData,
    GameUserData
} from "../../schemas/game";
import DataContext from "../../contexts/data";

import "./index.scss";

export interface Message {
    level: "INFO" | "WARNING" | "ERROR",
    context: string
};

let ws: WebSocket | undefined;

const dealWs = (
    setGameData: Dispatch<SetStateAction<GameData | undefined>>,
    setUserData: Dispatch<SetStateAction<GameUserData>>,
    setMessageArray: Dispatch<SetStateAction<Array<Message>>>
) => {
    return (event: MessageEvent) => {
        const data: {
            type: "DATA" | "USER" | "REJECT" | "INFO" | "WARNING" | "ERROR" | "END",
            data: GameData | GameUserData | string
        } = JSON.parse(event.data);
        console.log(data);
        switch (data.type) {
            case "DATA":
                setGameData(data.data as GameData);
                break;
            case "USER":
                setUserData(data.data as GameUserData);
                break;
            case "REJECT":
                alert(data.data);
                ws?.close();
                break;
            case "INFO":
            case "WARNING":
            case "ERROR":
                setMessageArray(origin => [...origin, {
                    level: data.type,
                    context: data.data,
                } as Message])
                break;
            case "END":
                setMessageArray(origin => [...origin, {
                    level: "INFO",
                    context: data.data,
                } as Message])
                break;
        }
    };
}

export default function Game(): ReactElement {
    const ref = createRef<HTMLDivElement>();
    const [searchParams,] = useSearchParams();
    const [gameData, setGameData] = useState<GameData | undefined>(undefined);
    const [gameUserData, setUserData] = useState<GameUserData>({ host: -1, users: [] });
    const [messageArray, setMessageArray] = useState<Array<Message>>([]);
    const setNavigate = useNavigate();
    const { user } = useContext(DataContext);

    const code = searchParams.get("code");
    if (code === null) {
        setNavigate("/");
    }

    useEffect(() => {
        if (ws !== undefined || code === null) return;
        let url = process.env.REACT_APP_API_END_POINT ?? window.location.origin;
        url = url.startsWith("http") ? url.replace("http", "ws") : `${window.location.origin.replace("http", "ws")}${process.env.REACT_APP_API_END_POINT}`;

        ws = new WebSocket(`${url}/game/ws/${code}`);
        ws.addEventListener("open", () => {
            if (ws === undefined) return;
            ws.send(localStorage.getItem("access_token") ?? "");
        });
        ws.addEventListener("message", dealWs(
            setGameData,
            setUserData,
            setMessageArray,
        ));
        ws.addEventListener("close", () => {
            setNavigate("/");
        });
    }, [code, setGameData, setUserData, setMessageArray, setNavigate]);
    useEffect(() => () => {
        ws?.close();
        ws = undefined;
    }, []);

    const scrollPage = (page: number) => {
        const target = ref.current;
        if (target === null) return;
        target.scroll(0, page === 0 ? 0 : target.scrollHeight);
    }

    const isHost = user?.id === gameUserData.host;

    return (
        <div ref={ref} id="game">
            {
                ws && gameData ? 
                <GameBlock
                    ws={ws}
                    gameData={gameData}
                    gameUserData={gameUserData}
                    scrollPage={scrollPage}
                /> : <div className="gameBlock">
                    <h3>Game</h3>
                    {isHost ? <button className="wait" onClick={() => {
                        if (ws === undefined) return;
                        ws.send(JSON.stringify({
                            "type": "START"
                        }));
                    }}>開始遊戲</button> : <div className="wait">等待房主開始遊戲...</div>}
                    <button className="pageButton" onClick={() => { scrollPage(1); }}>Next</button>
                </div>
            }
            <InfoBlock
                gameData={gameData}
                gameUserData={gameUserData}
                messageArray={messageArray}
                scrollPage={scrollPage}
            />
        </div>
    );
}
