import { Action } from "redux";

export const initialState = {
    isAuth: !!localStorage.getItem("access_token"),
};

export const SET_LOGIN = 'SET_LOGIN';

interface SetLoginAction extends Action<typeof SET_LOGIN> {
    payload: boolean;
}

export const setIsAuth = (value: boolean): SetLoginAction => {
    return {
        payload: value,
        type: SET_LOGIN,
    };
};

type AuthAction = SetLoginAction;

export const AuthReducer = (state = initialState, action: AuthAction) => {
    switch (action.type) {
        case SET_LOGIN:
            return { ...state, isAuth: action.payload };
        default:
            return state;
    }
};

export default AuthReducer;
