import { Context, createContext } from "react";

type Functions = Context<{
    SwitchLoading: (status: boolean) => void
}>

const FunctionContext: Functions = createContext({
    SwitchLoading: (status: boolean) => {}
});

export default FunctionContext;
