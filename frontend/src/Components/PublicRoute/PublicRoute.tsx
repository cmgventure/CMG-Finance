import {useSelector} from "react-redux";
import {Navigate} from "react-router-dom";
import {FC} from "react";
import {RootState} from "~/Store/Store.ts";

interface PublicRouteProps {
    component: FC
}

export const PublicRoute: FC<PublicRouteProps> = ({component: Component}) => {
    const isAuthenticated = useSelector((state: RootState) => state.auth.isAuth);
    if (isAuthenticated){
        return <Navigate to={'/admin/categories'}/>;
    }
    return <Component/>;
}
