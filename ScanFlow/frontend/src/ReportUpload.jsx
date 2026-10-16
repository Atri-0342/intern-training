
import { useState } from "react";
import { apiFetch } from "./api";

function getRadiologistId(token) {
    if (!token) {
        throw new Error("Please log in again.");
    }

    const parts = token.split(".");

    if (parts.length !== 3) {
        throw new Error("Invalid access token. Please log in again.");
    }

    const base64 = parts[1]
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const padded = base64.padEnd(
        base64.length + ((4 - (base64.length % 4)) % 4),
        "="
    );

    let claims;

    try {
        claims = JSON.parse(atob(padded));
    } catch {
        throw new Error("Could not read the access token.");
    }

    if (!claims.sub || claims.role !== "radiologist") {
        throw new Error("You must be logged in as a radiologist.");
    }

    if (claims.exp && claims.exp <= Math.floor(Date.now() / 1000)) {
        throw new Error("Your session has expired. Please log in again.");
    }

    return claims.sub;
}

export function ReportUpload({ accessToken }) {
    const [scanId, setScanId] = useState("");
    const [findings, setFindings] = useState("");
    const [finalizedAt, setFinalizedAt] = useState("");
    const [pdfFile, setPdfFile] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    async function handleSubmit(event) {
        event.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const radiologistId = getRadiologistId(accessToken);

            if (!pdfFile) {
                throw new Error("Please select a PDF report.");
            }

            if (pdfFile.size > 20 * 1024 * 1024) {
                throw new Error("The PDF must be 20 MB or smaller.");
            }

            const formData = new FormData();

            formData.append("id", crypto.randomUUID());
            formData.append("scan_id", scanId.trim());
            formData.append("findings", findings.trim());
            formData.append("radiologist_id", radiologistId);

            if (finalizedAt) {
                const date = new Date(finalizedAt);

                if (Number.isNaN(date.getTime())) {
                    throw new Error("Please enter a valid finalized date.");
                }

                formData.append("finalized_at", date.toISOString());
            }

            formData.append("file", pdfFile);

            const data = await apiFetch("/v1/reports/", {
                method: "POST",
                headers: {
                    "Idempotency-Key": crypto.randomUUID(),
                },
                body: formData,
            });

            setSuccess(`Report created successfully. ID: ${data.id}`);
            setScanId("");
            setFindings("");
            setFinalizedAt("");
            setPdfFile(null);
            event.target.reset();
        } catch (err) {
            setError(err.message || "Failed to upload report.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div>
            <h2>Upload Report</h2>

            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="scanId">Scan ID:</label>
                    <input
                        id="scanId"
                        value={scanId}
                        onChange={(event) => setScanId(event.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="findings">Findings:</label>
                    <textarea
                        id="findings"
                        value={findings}
                        onChange={(event) => setFindings(event.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="finalizedAt">Finalized at:</label>
                    <input
                        id="finalizedAt"
                        type="datetime-local"
                        value={finalizedAt}
                        onChange={(event) => setFinalizedAt(event.target.value)}
                    />
                </div>

                <div>
                    <label htmlFor="pdfFile">Report PDF:</label>
                    <input
                        id="pdfFile"
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={(event) =>
                            setPdfFile(event.target.files?.[0] || null)
                        }
                        required
                    />
                </div>

                <button type="submit" disabled={loading}>
                    {loading ? "Uploading..." : "Upload Report"}
                </button>
            </form>

            {error && <p role="alert">Error: {error}</p>}
            {success && <p role="status">{success}</p>}
        </div>
    );
}
