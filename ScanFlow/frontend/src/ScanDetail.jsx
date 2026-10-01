import { useEffect, useState } from "react";
import { apiFetch } from "./api";

export function ScanDetail({ scanId }) {
    const [scan, setScan] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadScan();
    }, [scanId]);

    async function loadScan() {
        setLoading(true);
        setError(null);

        try {
            const data = await apiFetch(`/v1/scans/${scanId}`);
            setScan(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <div>
                <p>Loading scan...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <p role="alert">Error: {error}</p>
            </div>
        );
    }

    if (!scan) {
        return null;
    }

    return (
        <div>
            <h2>Scan Detail</h2>

            <div>
                <p>
                    <strong>Scan ID:</strong> {scan.id}
                </p>

                <p>
                    <strong>Patient ID:</strong> {scan.patient_id}
                </p>

                <p>
                    <strong>Modality:</strong> {scan.modality}
                </p>

                <p>
                    <strong>Body Part:</strong> {scan.body_part}
                </p>

                <p>
                    <strong>Acquired At:</strong> {scan.acquired_at}
                </p>

                <p>
                    <strong>Uploaded At:</strong>{" "}
                    {scan.uploaded_at ?? "Not uploaded"}
                </p>

                <p>
                    <strong>Status:</strong> {scan.status}
                </p>

                <p>
                    <strong>Created At:</strong> {scan.created_at}
                </p>

                <p>
                    <strong>Updated At:</strong> {scan.updated_at}
                </p>
            </div>
        </div>
    );
}