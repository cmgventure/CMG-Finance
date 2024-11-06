import { useNavigate } from 'react-router-dom';
import styles from './Navigation.module.scss';
import { useDispatch } from "react-redux";
import { Button } from "../Button";
import { FC } from "react";
import {setIsAuth} from "~/Store/Reducers/AuthReducer.ts";

export const Navigation: FC = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        dispatch(setIsAuth(false));
        window.location.href = "/admin";
    };

    return (
        <>
            <div className={styles.nav}>
                <span className={styles.categoryLink} onClick={() => navigate('/admin/categories')}>
                    List of categories
                </span>
                <Button onClick={handleLogout} variant='active' className={styles.logoutButton}>
                    Logout
                </Button>
            </div>
        </>
    );
};
