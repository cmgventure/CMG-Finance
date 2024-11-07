import {useSelector} from "react-redux";
import {Navigate} from "react-router-dom";
import {FC} from "react";
import {RootState} from "~/Store/Store.ts";

interface PrivateRouteProps {
    component: FC
}

export const PrivateRoute: FC<PrivateRouteProps> = ({component: Component}) => {
    const isAuthenticated = useSelector((state: RootState) => state.auth.isAuth);
    if (!isAuthenticated){
        return <Navigate to={'/'}/>;
    }
    return <Component/>;
}