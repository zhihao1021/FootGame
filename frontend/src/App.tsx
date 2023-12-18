import axios from "axios";
import { jwtDecode } from "jwt-decode";
import {
    ReactElement,
    useEffect,
    useState
} from "react";
import {
    Routes,
    Route,
    useNavigate,
    Navigate,
    NavigateFunction,
} from "react-router-dom";

import FunctionContext from "./contexts/function";
import DataContext from "./contexts/data";

import Loading from "./components/loading";
import Login from "./components/login";
import Logout from "./components/logout";
import Home from "./components/home";
import Game from "./components/game";

import Token from "./schemas/token";
import JWTData from "./schemas/jwt";

import "./App.scss"

async function refreshToken(
    SwitchLoading: (status: boolean) => void,
    setNavigate: NavigateFunction,
    setUserData: (data: JWTData) => void
) {
    SwitchLoading(true)
    try {
        const jwt = localStorage.getItem("access_token");
        if (jwt === null) throw Error("JWT not found");
        const decodeJWT: JWTData = jwtDecode(jwt);
        if ((decodeJWT.exp ?? 0) - (Date.now() / 1000) < 3600 * 24) {
            const response = await axios.post("/oauth/refresh");
            const data: Token = response.data;
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("token_type", data.token_type);
            setUserData(jwtDecode(data.access_token) as JWTData)
        }
        else {
            setUserData(decodeJWT);
        }
    }
    catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token_type");
        setNavigate("/login");
    }
    finally {
        SwitchLoading(false);
    }
}

let loadingCount = 0;

export default function App(): ReactElement {
    const [showLoading, setLoading] = useState<boolean>(false);
    const [userData, setUserData] = useState<JWTData | undefined>();
    const setNavigate = useNavigate();

    const SwitchLoading = (status: boolean) => {
        loadingCount += status ? 1 : -1;
        setLoading(loadingCount > 0);
    }

    useEffect(() => {
        refreshToken(SwitchLoading, setNavigate, setUserData);
    }, [setNavigate, setUserData]);

    return (
        <div id="app">
            <Loading show={showLoading} />
            <FunctionContext.Provider value={{
                SwitchLoading: SwitchLoading
            }}>
                <DataContext.Provider value={{
                    user: userData
                }}>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/login" element={<Login setUserData={setUserData} />} />
                        <Route path="/logout" element={<Logout setUserData={setUserData} />} />
                        <Route path="/game" element={<Game />} />
                        <Route path="*" element={<Navigate to={"/"} replace/>}></Route>
                    </Routes>
                </DataContext.Provider>
            </FunctionContext.Provider>            
        </div>
    );
}
