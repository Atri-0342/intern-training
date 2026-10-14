import { useState } from "react";
import { apiFetch } from "../api";

export function Register() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState("clinician");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    async function handleRegister(event) {
        event.preventDefault();

        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const data = await apiFetch("/v1/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    email,
                    password,
                    role,
                }),
            });

            setSuccess(data.message || "Registration successful.");

            setEmail("");
            setPassword("");
            setRole("clinician");
        } catch (err) {
            setError(err.message || "Registration failed.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div>
            <h2>Register</h2>

            <form onSubmit={handleRegister}>
                <div>
                    <label htmlFor="email">Email:</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        autoComplete="email"
                        required
                    />
                </div>

                <div>
                    <label htmlFor="password">Password:</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        autoComplete="new-password"
                        required
                    />
                </div>

                <div>
                    <label htmlFor="role">Role:</label>
                    <select
                        id="role"
                        value={role}
                        onChange={(event) => setRole(event.target.value)}
                    >
                        <option value="clinician">Clinician</option>
                        <option value="radiologist">Radiologist</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>

                <button type="submit" disabled={loading}>
                    {loading ? "Registering..." : "Register"}
                </button>
            </form>

            {error && <p role="alert">Error: {error}</p>}
            {success && <p role="status">{success}</p>}
        </div>
    );
}