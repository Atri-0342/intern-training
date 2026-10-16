
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "./api";

const USE_ANALYSIS_WEBSOCKET =
    import.meta.env.VITE_USE_ANALYSIS_WEBSOCKET === "true";

const MODALITIES = ["CT", "MRI", "X-ray"];
const SCAN_STATUSES = ["uploaded", "processing", "completed", "failed"];

const formatDateTimeLocal = (value) => {
    if (!value) return "";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return "";

    const localDate = new Date(
        date.getTime() - date.getTimezoneOffset() * 60000,
    );

    return localDate.toISOString().slice(0, 16);
};

export function ScanDetail({ scanId, role }) {
    const [scan, setScan] = useState(null);
    const [analysis, setAnalysis] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const [updateError, setUpdateError] = useState(null);
    const [updateSuccess, setUpdateSuccess] = useState(null);

    const [patientId, setPatientId] = useState("");
    const [modality, setModality] = useState("CT");
    const [bodyPart, setBodyPart] = useState("");
    const [acquiredAt, setAcquiredAt] = useState("");
    const [statusValue, setStatusValue] = useState("uploaded");
    const [replacementFile, setReplacementFile] = useState(null);

    const fileInputRef = useRef(null);

    const canUpdate = role === "clinician";

    useEffect(() => {
        let cancelled = false;

        async function loadScan() {
            setLoading(true);
            setError(null);
            setScan(null);
            setAnalysis(null);
            setEditing(false);
            setUpdateError(null);
            setUpdateSuccess(null);

            try {
                const data = await apiFetch(`/v1/scans/${scanId}`);

                if (!cancelled) {
                    setScan(data);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(err.message);
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        if (scanId) {
            loadScan();
        } else {
            setLoading(false);
            setError("A scan ID is required.");
        }

        return () => {
            cancelled = true;
        };
    }, [scanId]);

    function openUpdateForm() {
        if (!scan || !canUpdate) return;

        setPatientId(scan.patient_id ?? "");
        setModality(scan.modality ?? "CT");
        setBodyPart(scan.body_part ?? "");
        setAcquiredAt(formatDateTimeLocal(scan.acquired_at));
        setStatusValue(scan.status ?? "uploaded");
        setReplacementFile(null);
        setUpdateError(null);
        setUpdateSuccess(null);
        setEditing(true);
    }

    function cancelUpdate() {
        setEditing(false);
        setUpdateError(null);
        setReplacementFile(null);

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    }

    async function handleUpdateSubmit(event) {
        event.preventDefault();

        if (!canUpdate) {
            setUpdateError("You are not authorized to update scans.");
            return;
        }

        if (!scan) return;

        setSaving(true);
        setUpdateError(null);
        setUpdateSuccess(null);

        try {
            if (!patientId.trim()) {
                throw new Error("Patient ID is required.");
            }

            if (!bodyPart.trim()) {
                throw new Error("Body part is required.");
            }

            if (!acquiredAt) {
                throw new Error("Acquisition date and time are required.");
            }

            const acquiredDate = new Date(acquiredAt);

            if (Number.isNaN(acquiredDate.getTime())) {
                throw new Error("Enter a valid acquisition date and time.");
            }

            const formData = new FormData();

            formData.append("patient_id", patientId.trim());
            formData.append("modality", modality);
            formData.append("body_part", bodyPart.trim());
            formData.append("acquired_at", acquiredDate.toISOString());
            formData.append("status_value", statusValue);

            if (replacementFile) {
                const allowedTypes = [
                    "application/pdf",
                    "image/jpeg",
                    "image/png",
                ];

                const maxFileSize = 20 * 1024 * 1024;

                if (!allowedTypes.includes(replacementFile.type)) {
                    throw new Error("Only PDF, JPG, and PNG files are allowed.");
                }

                if (replacementFile.size > maxFileSize) {
                    throw new Error("File size must be 20 MB or less.");
                }

                formData.append("file", replacementFile);
            }

            const data = await apiFetch(`/v1/scans/${scanId}`, {
                method: "PATCH",
                body: formData,
            });

            setScan(data);
            setEditing(false);
            setReplacementFile(null);
            setUpdateSuccess("Scan updated successfully.");

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        } catch (err) {
            setUpdateError(err.message);
        } finally {
            setSaving(false);
        }
    }

//     useEffect(() => {
//         const controller = new AbortController();

//         let timerId = null;
//         let cancelled = false;
//         let attempts = 0;

//         const MAX_ATTEMPTS = 10;
//         const MAX_DELAY = 15000;

//         console.log(
//             "Analysis polling started",
//         );

//         async function pollAnalysis() {
//             if (cancelled) {
//                 return;
//             }

//             attempts += 1;

//             console.log(
//                 `Analysis polling attempt ${attempts}`,
//             );

//             try {
//                 const data = await apiFetch(
//                     `/v1/scans/${scanId}/analysis`,
//                     {
//                         signal: controller.signal,
//                     },
//                 );

//                 if (cancelled) {
//                     return;
//                 }

//                 console.log(
//                     "Analysis polling:",
//                     data,
//                 );

//                 setAnalysis(data);

//                 if (
//                     data.status === "done" ||
//                     data.status === "failed"
//                 ) {
//                     console.log(
//                         `Analysis polling stopped: ${data.status}`,
//                     );

//                     return;
//                 }

//                 if (
//                     attempts >= MAX_ATTEMPTS
//                 ) {
//                     console.log(
//                         "Analysis polling stopped: maximum attempts reached",
//                     );

//                     return;
//                 }

//                 const delay = Math.min(
//                     2000 *
//                         2 ** (attempts - 1),
//                     MAX_DELAY,
//                 );

//                 console.log(
//                     `Next analysis poll in ${delay}ms`,
//                 );

//                 timerId =
//                     window.setTimeout(
//                         pollAnalysis,
//                         delay,
//                     );
//             } catch (err) {
//     if (controller.signal.aborted || cancelled) return;

//     if (err.message === "Analysis job not found") {
//         console.log("No analysis job found. Starting analysis...");

//         try {
//             const started = await apiFetch(
//                 `/v1/scans/${scanId}/analyze`,
//                 {
//                     method: "POST",
//                     signal: controller.signal,
//                 },
//             );

//             if (cancelled) return;

//             console.log("Analysis started:", started);
//             setAnalysis(started);

//             timerId = window.setTimeout(pollAnalysis, 2000);
//             return;
//         } catch (startErr) {
//             if (controller.signal.aborted || cancelled) return;

//             console.error("Failed to start analysis:", startErr);
//         }
//     }

//     console.error("Analysis polling error:", err);

//     if (attempts >= MAX_ATTEMPTS) {
//         console.log("Analysis polling stopped: maximum attempts reached");
//         return;
//     }

//     const delay = Math.min(
//         2000 * 2 ** (attempts - 1),
//         MAX_DELAY,
//     );

//     console.log(`Retrying analysis poll in ${delay}ms`);
//     timerId = window.setTimeout(pollAnalysis, delay);
// }
//         }

//         pollAnalysis();

//         return () => {
//             cancelled = true;

//             if (timerId !== null) {
//                 window.clearTimeout(
//                     timerId,
//                 );

//                 timerId = null;
//             }

//             controller.abort();

//             console.log(
//                 "Analysis polling cleanup",
//             );
//         };
//     }, [scanId]);

    useEffect(() => {
        if (!USE_ANALYSIS_WEBSOCKET) {
            return;
        }

        let socket = null;
        let reconnectTimer = null;
        let cancelled = false;

        // Prevent reconnect after an intentional terminal-state close.
        let terminal = false;

        let reconnectAttempt = 0;

        const MAX_RECONNECT_DELAY = 15000;

        const TERMINAL_STATUSES = new Set([
            "done",
            "failed",
        ]);

        const getReconnectDelay = () => {
            const delay = Math.min(
                2000 * 2 ** reconnectAttempt,
                MAX_RECONNECT_DELAY,
            );

            reconnectAttempt += 1;

            return delay;
        };

        const getWebSocketUrl = (ticket) => {
            const apiBaseUrl =
                import.meta.env.VITE_API_BASE_URL ||
                window.location.origin;

            const url = new URL(
                `/v1/ws/scans/${scanId}`,
                apiBaseUrl,
            );

            url.protocol =
                url.protocol === "https:"
                    ? "wss:"
                    : "ws:";

            url.searchParams.set("ticket", ticket);

            return url.toString();
        };

        const closeSocket = () => {
            if (socket) {
                socket.close();
                socket = null;
            }
        };

        const clearReconnectTimer = () => {
            if (reconnectTimer !== null) {
                window.clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        const fetchCurrentStatus = async () => {
            try {
                const response = await apiFetch(
                    `/v1/scans/${scanId}/analysis`,
                );

                setAnalysis(response);

                if (TERMINAL_STATUSES.has(response.status)) {
                    terminal = true;
                    clearReconnectTimer();
                    closeSocket();
                }

                return response;
            } catch (error) {
                // No AnalysisJob exists yet.
                // Start analysis for this scan.
                if (error.status === 404) {
                    try {
                        const response = await apiFetch(
                            `/v1/scans/${scanId}/analyze`,
                            {
                                method: "POST",
                            },
                        );

                        setAnalysis(response);

                        console.log(
                            "Analysis started:",
                            response,
                        );

                        return response;
                    } catch (startError) {
                        console.error(
                            "Failed to start analysis:",
                            startError,
                        );

                        return null;
                    }
                }

                console.error(
                    "Failed to fetch analysis status:",
                    error,
                );

                return null;
            }
        };

        const connect = async () => {
            if (cancelled || terminal) {
                return;
            }

            if (!navigator.onLine) {
                return;
            }

            if (document.visibilityState === "hidden") {
                return;
            }

            clearReconnectTimer();

            try {
                /*
                 * First authenticate normally over HTTP.
                 * apiFetch should attach the JWT Authorization header.
                 */
                const ticketResponse = await apiFetch(
                    `/v1/ws/tickets?scan_id=${encodeURIComponent(scanId)}`,
                    {
                        method: "POST",
                    },
                );

                if (cancelled || terminal) {
                    return;
                }

                const ticket = ticketResponse.ticket;

                socket = new WebSocket(
                    getWebSocketUrl(ticket),
                );

                socket.onopen = async () => {
                    console.log(
                        "Analysis WebSocket connected",
                    );

                    /*
                     * Reset backoff after a successful connection.
                     */
                    reconnectAttempt = 0;

                    /*
                     * Synchronize current state in case the job
                     * changed before the WebSocket connected.
                     */
                    const currentStatus =
                        await fetchCurrentStatus();

                    if (
                        currentStatus &&
                        TERMINAL_STATUSES.has(currentStatus.status)
                    ) {
                        terminal = true;
                        clearReconnectTimer();
                        closeSocket();
                    }
                };

                socket.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);

                        setAnalysis((previous) => ({
                            ...previous,
                            ...message,
                        }));

                        if (TERMINAL_STATUSES.has(message.status)) {
                            console.log(
                                `Analysis reached terminal status: ${message.status}`,
                            );

                            /*
                             * Mark terminal BEFORE closing the socket.
                             * The onclose handler will then know that this
                             * was intentional and will not reconnect.
                             */
                            terminal = true;

                            clearReconnectTimer();
                            closeSocket();
                        }
                    } catch (error) {
                        console.error(
                            "Invalid WebSocket message:",
                            error,
                        );
                    }
                };

                socket.onerror = (error) => {
                    console.error(
                        "Analysis WebSocket error:",
                        error,
                    );
                };

                socket.onclose = () => {
                    socket = null;

                    /*
                     * Do not reconnect when:
                     *
                     * 1. Component was unmounted.
                     * 2. Analysis reached done/failed.
                     */
                    if (cancelled || terminal) {
                        return;
                    }

                    if (!navigator.onLine) {
                        return;
                    }

                    if (document.visibilityState === "hidden") {
                        return;
                    }

                    /*
                     * Unexpected close:
                     * reconnect using exponential backoff.
                     */
                    const delay = getReconnectDelay();

                    console.log(
                        `Analysis WebSocket closed unexpectedly. Reconnecting in ${delay}ms`,
                    );

                    reconnectTimer = window.setTimeout(
                        () => {
                            connect();
                        },
                        delay,
                    );
                };
            } catch (error) {
                console.error(
                    "Failed to create WebSocket:",
                    error,
                );

                if (
                    cancelled ||
                    terminal ||
                    !navigator.onLine ||
                    document.visibilityState === "hidden"
                ) {
                    return;
                }

                const delay = getReconnectDelay();

                reconnectTimer = window.setTimeout(
                    () => {
                        connect();
                    },
                    delay,
                );
            }
        };

        const handleOffline = () => {
            console.log(
                "Browser offline — closing analysis WebSocket",
            );

            clearReconnectTimer();
            closeSocket();
        };

        const handleOnline = () => {
            console.log(
                "Browser online — reconnecting analysis WebSocket",
            );

            if (cancelled || terminal) {
                return;
            }

            connect();
        };

        const handleVisibilityChange = async () => {
            if (document.visibilityState === "hidden") {
                console.log(
                    "Tab backgrounded — closing analysis WebSocket",
                );

                clearReconnectTimer();
                closeSocket();

                return;
            }

            if (document.visibilityState === "visible") {
                console.log(
                    "Tab visible — synchronizing analysis status",
                );

                if (terminal) {
                    return;
                }

                const currentStatus =
                    await fetchCurrentStatus();

                if (
                    currentStatus &&
                    TERMINAL_STATUSES.has(currentStatus.status)
                ) {
                    terminal = true;
                    clearReconnectTimer();
                    closeSocket();

                    return;
                }

                connect();
            }
        };

        window.addEventListener("offline", handleOffline);
        window.addEventListener("online", handleOnline);

        document.addEventListener(
            "visibilitychange",
            handleVisibilityChange,
        );

        connect();

        return () => {
            cancelled = true;

            clearReconnectTimer();

            window.removeEventListener("offline", handleOffline);
            window.removeEventListener("online", handleOnline);

            document.removeEventListener(
                "visibilitychange",
                handleVisibilityChange,
            );

            closeSocket();
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
                    <strong>Created At:</strong>{" "}
                    {scan.created_at ?? "Not provided by API"}
                </p>

                <p>
                    <strong>Updated At:</strong>{" "}
                    {scan.updated_at ?? "Not provided by API"}
                </p>

                <p>
                    <strong>Analysis Status:</strong>{" "}
                    {analysis?.status ?? "Not started"}
                </p>

                {updateSuccess && (
                    <p role="status">{updateSuccess}</p>
                )}

                {canUpdate && !editing && (
                    <button
                        type="button"
                        onClick={openUpdateForm}
                    >
                        Update Scan
                    </button>
                )}

                {canUpdate && editing && (
                    <form onSubmit={handleUpdateSubmit}>
                        <h3>Update Scan</h3>

                        {updateError && (
                            <p role="alert">{updateError}</p>
                        )}

                        <div>
                            <label htmlFor="update-patient-id">
                                Patient ID
                            </label>
                            <input
                                id="update-patient-id"
                                type="text"
                                value={patientId}
                                onChange={(event) =>
                                    setPatientId(event.target.value)
                                }
                                required
                            />
                        </div>

                        <div>
                            <label htmlFor="update-modality">
                                Modality
                            </label>
                            <select
                                id="update-modality"
                                value={modality}
                                onChange={(event) =>
                                    setModality(event.target.value)
                                }
                                required
                            >
                                {MODALITIES.map((item) => (
                                    <option key={item} value={item}>
                                        {item}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label htmlFor="update-body-part">
                                Body Part
                            </label>
                            <input
                                id="update-body-part"
                                type="text"
                                value={bodyPart}
                                onChange={(event) =>
                                    setBodyPart(event.target.value)
                                }
                                required
                            />
                        </div>

                        <div>
                            <label htmlFor="update-acquired-at">
                                Acquired At
                            </label>
                            <input
                                id="update-acquired-at"
                                type="datetime-local"
                                value={acquiredAt}
                                onChange={(event) =>
                                    setAcquiredAt(event.target.value)
                                }
                                required
                            />
                        </div>

                        <div>
                            <label htmlFor="update-status">
                                Status
                            </label>
                            <select
                                id="update-status"
                                value={statusValue}
                                onChange={(event) =>
                                    setStatusValue(event.target.value)
                                }
                                required
                            >
                                {SCAN_STATUSES.map((item) => (
                                    <option key={item} value={item}>
                                        {item}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label htmlFor="update-scan-file">
                                Replace Scan File (optional)
                            </label>
                            <input
                                ref={fileInputRef}
                                id="update-scan-file"
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                                onChange={(event) =>
                                    setReplacementFile(
                                        event.target.files?.[0] ?? null,
                                    )
                                }
                            />
                            <p>
                                Accepted formats: PDF, JPG, PNG. Maximum size: 20 MB.
                            </p>
                        </div>

                        <button type="submit" disabled={saving}>
                            {saving ? "Saving..." : "Save Changes"}
                        </button>

                        <button
                            type="button"
                            onClick={cancelUpdate}
                            disabled={saving}
                        >
                            Cancel
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
