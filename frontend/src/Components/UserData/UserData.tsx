import { useSelector } from "react-redux";
import styles from './userData.module.scss';
import {FC} from "react";
import {RootState} from "~/Store/Store.ts";

export const UserData: FC = () => {
    const { userData, isAuth } = useSelector((state: RootState) => state.auth);
    if (!userData) return null;

    if (isAuth) {
        return (
            <div className={styles.nav}>
                <ul>
                    <li>Email: {userData.email}</li>
                </ul>
            </div>
        );
    } else {
        return null;
    }
};
