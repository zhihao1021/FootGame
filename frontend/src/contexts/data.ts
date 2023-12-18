import { Context, createContext } from "react";
import UserData from "./user";

type Datas = Context<{
    user?: UserData
}>;

const DataContext: Datas = createContext({});

export default DataContext;
