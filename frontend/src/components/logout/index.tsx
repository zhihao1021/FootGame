import { ReactElement, useEffect } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import JWTData from "../../schemas/jwt";

type propsType = Readonly<{
    setUserData: (data?: JWTData) => void
}>;

export default function Logout(props: propsType): ReactElement {
    const { setUserData } = props;
    const setNavigate = useNavigate();

    useEffect(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token_type");
        setUserData(undefined);
        setNavigate("/login")
    }, [setNavigate, setUserData])

    return <Navigate to={"/login"} replace/>;
}
