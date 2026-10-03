import { useEffect, useState } from "react";
import { LoginScreen } from "./LoginScreen";
import { ScanList } from "./ScanList";
import { UploadScreen } from "./UploadScreen";
import {
    clearAuthToken,
    setUnauthorizedHandler,
} from "./api";

function App() {
    const [loggedIn, setLoggedIn] = useState(false);

    useEffect(() => {
        setUnauthorizedHandler(() => {
            setLoggedIn(false);
        });

        return () => {
            setUnauthorizedHandler(null);
        };
    }, []);

    function handleLoginSuccess() {
        setLoggedIn(true);
    }

    function handleLogout() {
        clearAuthToken();
        setLoggedIn(false);
    }

    if (!loggedIn) {
        return (
            <LoginScreen
                onLoginSuccess={handleLoginSuccess}
            />
        );
    }

    return (
        <div>
            <h1>ScanFlow</h1>

            <button onClick={handleLogout}>
                Logout
            </button>

            <UploadScreen />
        </div>
    );
}

export default App;