import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LoginPage from "~/pages/LoginPage/LoginPage.tsx";
import CategoriesPage from "~/pages/CategoriesPage/CategoriesPage.tsx";
import {PublicRoute} from "~/Components/PublicRoute";
import {Navigation} from "~/Components/Navigation";
import {useSelector} from "react-redux";
import {RootState} from "~/Store/Store.ts";
import {Toaster} from "react-hot-toast";
import {PrivateRoute} from "~/Components/PrivateRoute";

const AppRouter = () => {
    const isAuth = useSelector((state: RootState) => state.auth.isAuth);

    return (
        <Router>
            {isAuth && <Navigation/>}
            <Routes>
                <Route path="/admin/categories" element={<PrivateRoute component={CategoriesPage}/>} />
                <Route path="/" element={<PublicRoute  component={LoginPage}/>} />
            </Routes>
            <Toaster position="top-right" />
        </Router>
    );
};

export default AppRouter;
