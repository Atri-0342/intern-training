
import { useState } from "react";
import { apiFetch, setAuthToken } from "./api";

export function LoginScreen({ onLoginSuccess }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [submit, setSubmit] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();
        setError(null);
        setSubmit(true);

        try {
            const data = await apiFetch("/v1/auth/token", {
                method: "POST",
                body: JSON.stringify({ email, password }),
            });

            setAuthToken(data.access_token);

            // Decode the JWT payload for frontend role-based UI.
            const base64Payload = data.access_token
                .split(".")[1]
                .replace(/-/g, "+")
                .replace(/_/g, "/");

            const payload = JSON.parse(
                atob(
                    base64Payload +
                    "=".repeat((4 - base64Payload.length % 4) % 4)
                )
            );

            onLoginSuccess({
                userId: payload.sub,
                role: payload.role,
            });
        } catch (err) {
            setAuthToken(null);
            setError(err.message);
        } finally {
            setSubmit(false);
        }
    }

    return (
        <form onSubmit={handleSubmit}>
            <h1>Scanflow Login</h1>

            {error && (
                <p role="alert" style={{ color: "red" }}>
                    {error}
                </p>
            )}

            <label>
                Email:
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
            </label>

            <label>
                Password:
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </label>

            <button type="submit" disabled={submit}>
                {submit ? "Logging in..." : "Login"}
            </button>
        </form>
    );
}
