import {FC, ReactNode, useEffect} from "react";
import {useDispatch} from "react-redux";
import {setIsAuth} from "~/Store/Reducers/AuthReducer.ts";

interface AuthProviderProps {
    children: ReactNode
}

export const AuthProvider: FC<AuthProviderProps> = ({children}) => {
    const token = localStorage.getItem('access_token')
    const dispatch = useDispatch();

    // With me
    // const getUserData = async () => {
    //     if (token) {
    //         const userData = await userMe(token);
    //         if (userData) {
    //             dispatch(setIsAuth(true));
    //             dispatch(setUserData(userData));
    //         }
    //     } else {
    //         dispatch(setIsAuth(false));
    //     }
    //     // We don`t need it
    //     // await handleUserData(token, dispatch);
    // }


    useEffect(() => {
        if (token) {
            dispatch(setIsAuth(true));
        } else {
            dispatch(setIsAuth(false));
        }
    }, [token, dispatch]);

    return <>{children}</>;
}
