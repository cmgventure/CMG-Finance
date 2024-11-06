import {configureStore} from "@reduxjs/toolkit";
import AuthReducer from "./Reducers/AuthReducer";


const store = configureStore({
    reducer: {
        auth: AuthReducer,
    },
});

export type RootState = ReturnType<typeof store.getState>;

export default store;
