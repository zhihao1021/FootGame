import {
    CSSProperties,
    ReactElement
} from "react";

import "./index.scss";

type propsType = Readonly<{
    show: boolean
}>;

export default function Loading(props: propsType): ReactElement {
    const { show } = props;

    return (
        <div id="loading" data-show={show}>
            <h3>Loading...</h3>
            <div className="dotBox">
                {Array.from(Array(12)).map((_,index) => (
                    <div
                        key={index}
                        style={{ "--delay": index } as CSSProperties}
                    />
                ))}
            </div>
        </div>
    );
}
