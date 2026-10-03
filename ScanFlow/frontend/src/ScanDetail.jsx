import { useEffect, useRef, useState } from "react";
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
useEffect(() => {
    const controller = new AbortController();

    const timerRef = useRef(null);
    let cancelled = false;
    let attempts = 0;

    const MAX_ATTEMPTS = 10;
    const MAX_DELAY = 15000;
    async function pollAnalysis() {
        if (cancelled) return;

        attempts += 1;

        try {
            const data = await apiFetch(
                `/v1/scans/${scanId}/analysis`,
                {
                    signal: controller.signal,
                }
            );

            if (cancelled) return;

            console.log("Analysis polling:", data);

            if (data.status === "done" || data.status === "failed") {
                console.log(
                    `Analysis polling stopped: ${data.status}`
                );
                return;
            }

            if (attempts >= MAX_ATTEMPTS) {
                console.log(
                    "Analysis polling stopped: maximum attempts reached"
                );
                return;
            }

            const delay = Math.min(
                2000 * 2 ** (attempts - 1),
                MAX_DELAY
            );

        timerRef.current = setTimeout(pollAnalysis, delay);
        } catch (err) {
            if (controller.signal.aborted || cancelled) {
                return;
            }

            console.error("Analysis polling error:", err);

            if (attempts >= MAX_ATTEMPTS) {
                console.log(
                    "Analysis polling stopped: maximum attempts reached"
                );
                return;
            }

            const delay = Math.min(
                2000 * 2 ** (attempts - 1),
                MAX_DELAY
            );

            timerRef.current = setTimeout(pollAnalysis, delay);
        }
    }

    pollAnalysis();

    return () => {
        cancelled = true;

        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }

        controller.abort();
    };
}, [scanId]);


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
    return (
        <div>
            <p>No scan found.</p>
        </div>
    );
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