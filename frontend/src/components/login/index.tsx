import axios from "axios";
import { jwtDecode } from "jwt-decode";
import {
    ReactElement,
    useContext,
    useEffect,
    useState
} from "react";
import {
    useNavigate,
    NavigateFunction,
    useSearchParams
} from "react-router-dom";

import FunctionContext from "../../contexts/function";

import JWTData from "../../schemas/jwt";

import "./index.scss";

const DISCORD_REDIRECT_URI = process.env.REACT_APP_DISCORD_REDIRECT_URI;
const DISCORD_CLIENT_ID = process.env.REACT_APP_DISCORD_CLIENT_ID;

async function login(
    code: string,
    SwitchLoading: (status: boolean) => void,
    setError: (status: boolean) => void,
    setNavigate: NavigateFunction,
    setUserData: (data: JWTData) => void,
) {
    SwitchLoading(true)
    try {
        const response = await axios.post("/oauth/login", { code: code });
        const data: {
            access_token: string
            token_type: string
        } = response.data;
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type);
        setUserData(jwtDecode(data.access_token) as JWTData);
        setNavigate("/");
    }
    catch {
        setError(true);
    }
    finally {
        SwitchLoading(false);
    }
}

type propsType = Readonly<{
    setUserData: (data?: JWTData) => void
}>;

export default function Login(props: propsType): ReactElement {
    const [searchParams, setSearchParams] = useSearchParams();
    const [error, setError] = useState(false);
    const { SwitchLoading } = useContext(FunctionContext);
    const setNavigate = useNavigate();
    const { setUserData } = props;

    const code = searchParams.get("code");
    useEffect(() => {
        if (code == null) return;
        setSearchParams({})
        login(code, SwitchLoading, setError, setNavigate, setUserData);
    }, [code, SwitchLoading, setError, setNavigate, setUserData, setSearchParams]);

    return (
        <div id="login">
            <div className="box">
                <h2>Login</h2>
                <a href={`https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&response_type=code&redirect_uri=${DISCORD_REDIRECT_URI}&scope=identify`}>
                    <img alt="discord" src={`${process.env.PUBLIC_URL}/img/discord.png`}></img>
                </a>
                <div className="errorMessage" data-show={error}>登入失敗</div>
            </div>
        </div>
    );
}
