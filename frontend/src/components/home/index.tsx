import {
    ChangeEvent,
    KeyboardEvent,
    ReactElement,
    useContext,
    useState,
} from "react";
import {
    useNavigate,
    Link,
    Navigate,
} from "react-router-dom";

import DataContext from "../../contexts/data";

import "./index.scss";

export default function Home(): ReactElement {
    const [gameCode, setGameCode] = useState<string>("");
    const [errorMessage, setErrorMessage] = useState<string>("");
    const setNavigate = useNavigate();
    const { user } = useContext(DataContext);

    
    const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setGameCode(value);
        setErrorMessage(value === "" ? "請輸入Game Code。" : "");
    };

    const joinGame = () => {
        if (gameCode === "") {
            setErrorMessage("請輸入Game Code。")
            return;
        }
        setNavigate(`/game?code=${gameCode}`);
    };
    const onEnterDown = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") {
            joinGame();
        }
    };

    if (user === undefined) {
        return <Navigate to={"/"} replace />
    }
    

    return (
        <div id="home">
            <div className="box">
                <h2>Join/Create Game</h2>
                <div className="inputBox">
                    <input value={gameCode} onChange={onInputChange} onKeyDown={onEnterDown} placeholder="Game Code" />
                    <button onClick={joinGame}>Join</button>
                </div>
                <div className="errorMessage" data-show={errorMessage !== ""}>{errorMessage}</div>
                <div className="account">
                    {`Login as @${user?.display_name}.`} Not you? <Link to={"/logout"}>Logout</Link>
                </div>
            </div>
        </div>
    );
}
