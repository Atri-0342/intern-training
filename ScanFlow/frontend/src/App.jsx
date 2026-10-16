
import { useEffect, useState } from "react";
import { LoginScreen } from "./LoginScreen";
import { ScanList } from "./ScanList";
import { UploadScreen } from "./UploadScreen";
import { ReportList } from "./ReportList";

import {
    clearAuthToken,
    setUnauthorizedHandler,
} from "./api";

function App() {
    const [loggedIn, setLoggedIn] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
        setUnauthorizedHandler(() => {
            clearAuthToken();
            setLoggedIn(false);
            setCurrentUser(null);
        });

        return () => {
            setUnauthorizedHandler(null);
        };
    }, []);

    function handleLoginSuccess(user) {
        setCurrentUser({
            userId: user.userId,
            role: user.role,
        });

        setLoggedIn(true);
    }

    function handleLogout() {
        clearAuthToken();
        setCurrentUser(null);
        setLoggedIn(false);
    }

    if (!loggedIn || !currentUser) {
        return (
            <LoginScreen
                onLoginSuccess={handleLoginSuccess}
            />
        );
    }

    return (
        <div>
            <header>
                <h1>ScanFlow</h1>

                <p>
                    Role: <strong>{currentUser.role}</strong>
                </p>

                <button
                    type="button"
                    onClick={handleLogout}
                >
                    Logout
                </button>
            </header>

            {currentUser.role === "clinician" && (
                <UploadScreen
                    role={currentUser.role}
                />
            )}

            <ScanList
                role={currentUser.role}
            />

            <ReportList
                currentRole={currentUser.role}
            />
        </div>
    );
}

export default App;
