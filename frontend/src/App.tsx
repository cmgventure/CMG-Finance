import AppRouter from './AppRouter';
import store from './Store/Store';
import { Provider } from 'react-redux';
// import {AuthProvider} from "./Providers/AuthProvider";

const App = () => {
    return (
        <Provider store={store}>
            {/*<AuthProvider>*/}
                <AppRouter />
            {/*</AuthProvider>*/}
        </Provider>
    );
};

export default App;
