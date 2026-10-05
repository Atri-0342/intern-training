import { useEffect, useRef, useState } from "react";
import { apiFetch } from "./api";

const USE_ANALYSIS_WEBSOCKET =
  import.meta.env.VITE_USE_ANALYSIS_WEBSOCKET === "true";

export function ScanDetail({ scanId }) {
    const [scan, setScan] = useState(null);
    const [analysis, setAnalysis] = useState(null);

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

      if (
        TERMINAL_STATUSES.has(response.status)
      ) {
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
    if (
      cancelled ||
      terminal
    ) {
      return;
    }

    if (!navigator.onLine) {
      return;
    }

    if (
      document.visibilityState === "hidden"
    ) {
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

      if (
        cancelled ||
        terminal
      ) {
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
          TERMINAL_STATUSES.has(
            currentStatus.status,
          )
        ) {
          terminal = true;

          clearReconnectTimer();
          closeSocket();
        }
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(
            event.data,
          );

          setAnalysis((previous) => ({
            ...previous,
            ...message,
          }));

          if (
            TERMINAL_STATUSES.has(
              message.status,
            )
          ) {
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
        if (
          cancelled ||
          terminal
        ) {
          return;
        }

        if (!navigator.onLine) {
          return;
        }

        if (
          document.visibilityState === "hidden"
        ) {
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

    if (
      cancelled ||
      terminal
    ) {
      return;
    }

    connect();
  };

  const handleVisibilityChange = async () => {
    if (
      document.visibilityState === "hidden"
    ) {
      console.log(
        "Tab backgrounded — closing analysis WebSocket",
      );

      clearReconnectTimer();
      closeSocket();

      return;
    }

    if (
      document.visibilityState === "visible"
    ) {
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
        TERMINAL_STATUSES.has(
          currentStatus.status,
        )
      ) {
        terminal = true;

        clearReconnectTimer();
        closeSocket();

        return;
      }

      connect();
    }
  };

  window.addEventListener(
    "offline",
    handleOffline,
  );

  window.addEventListener(
    "online",
    handleOnline,
  );

  document.addEventListener(
    "visibilitychange",
    handleVisibilityChange,
  );

  connect();

  return () => {
    cancelled = true;

    clearReconnectTimer();

    window.removeEventListener(
      "offline",
      handleOffline,
    );

    window.removeEventListener(
      "online",
      handleOnline,
    );

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
                    <strong>Created At:</strong> {scan.created_at}
                </p>

                <p>
                    <strong>Updated At:</strong> {scan.updated_at}
                </p>

                <p>
                    <strong>Analysis Status:</strong>{" "}
                    {analysis?.status ?? "Not started"}
                </p>
            </div>
        </div>
    );
}