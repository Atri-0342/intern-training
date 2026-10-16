
import { useState, useEffect } from "react";
import { apiFetch } from "./api";

const REPORT_ROLES = {
    VIEW: ["clinician", "radiologist", "admin"],
    UPDATE: "radiologist",
    DELETE: "admin",
};

export function ReportList({ currentRole }) {
    const [reports, setReports] = useState([]);
    const [limit] = useState(10);
    const [offset, setOffset] = useState(0);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [selectedReport, setSelectedReport] = useState(null);
    const [modalType, setModalType] = useState("");
    const [modalLoading, setModalLoading] = useState(false);
    const [modalError, setModalError] = useState(null);
    const [saving, setSaving] = useState(false);

    const [form, setForm] = useState({
        scan_id: "",
        findings: "",
        radiologist_id: "",
        finalized_at: "",
    });

    const [pdfFile, setPdfFile] = useState(null);

    const canView = REPORT_ROLES.VIEW.includes(currentRole);
    const canUpdate = currentRole === REPORT_ROLES.UPDATE;
    const canDelete = currentRole === REPORT_ROLES.DELETE;

    useEffect(() => {
        if (canView) {
            load_reports();
        } else {
            setReports([]);
            setError("You are not authorized to view reports.");
        }
    }, [limit, offset, currentRole]);

    async function load_reports() {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();

            params.set("limit", String(limit));
            params.set("offset", String(offset));

            const data = await apiFetch(
                `/v1/reports?${params.toString()}`
            );

            setReports(Array.isArray(data) ? data : data.items ?? []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleViewReport(reportId) {
        if (!canView) return;

        setModalType("view");
        setSelectedReport(null);
        setModalError(null);
        setModalLoading(true);

        try {
            const report = await apiFetch(
                `/v1/reports/${reportId}`
            );

            setSelectedReport(report);
        } catch (err) {
            setModalError(err.message);
        } finally {
            setModalLoading(false);
        }
    }

    async function handleUpdateClick(reportId) {
        if (!canUpdate) return;

        setModalType("update");
        setSelectedReport(null);
        setModalError(null);
        setModalLoading(true);
        setPdfFile(null);

        try {
            const report = await apiFetch(
                `/v1/reports/${reportId}`
            );

            setSelectedReport(report);

            setForm({
                scan_id: report.scan_id || "",
                findings: report.findings || "",
                radiologist_id: report.radiologist_id || "",
                finalized_at: report.finalized_at
                    ? report.finalized_at.slice(0, 16)
                    : "",
            });
        } catch (err) {
            setModalError(err.message);
        } finally {
            setModalLoading(false);
        }
    }

    async function handleUpdateReport(event) {
        event.preventDefault();

        if (!canUpdate || !selectedReport) return;

        if (!pdfFile) {
            setModalError("Please select the replacement PDF file.");
            return;
        }

        if (pdfFile.type !== "application/pdf") {
            setModalError("Only PDF files are allowed.");
            return;
        }

        if (pdfFile.size > 20 * 1024 * 1024) {
            setModalError("PDF file size must be 20 MB or less.");
            return;
        }

        setSaving(true);
        setModalError(null);

        const formData = new FormData();

        formData.append("scan_id", form.scan_id);
        formData.append("findings", form.findings);
        formData.append("radiologist_id", form.radiologist_id);

        if (form.finalized_at) {
            formData.append(
                "finalized_at",
                new Date(form.finalized_at).toISOString()
            );
        }

        formData.append("file", pdfFile);

        try {
            const updatedReport = await apiFetch(
                `/v1/reports/${selectedReport.id}`,
                {
                    method: "PATCH",
                    body: formData,
                }
            );

            setReports((current) =>
                current.map((report) =>
                    report.id === updatedReport.id
                        ? updatedReport
                        : report
                )
            );

            closeModal();
        } catch (err) {
            setModalError(err.message);
        } finally {
            setSaving(false);
        }
    }

    async function handleDeleteReport(reportId) {
        if (!canDelete) return;

        const confirmed = window.confirm(
            "Are you sure you want to delete this report?"
        );

        if (!confirmed) return;

        setError(null);

        try {
            await apiFetch(
                `/v1/reports/${reportId}`,
                { method: "DELETE" }
            );

            const remainingReports = reports.filter(
                (report) => report.id !== reportId
            );

            setReports(remainingReports);

            if (remainingReports.length === 0 && offset > 0) {
                setOffset(Math.max(0, offset - limit));
            }
        } catch (err) {
            setError(err.message);
        }
    }

    function closeModal() {
        setSelectedReport(null);
        setModalType("");
        setModalError(null);
        setModalLoading(false);
        setPdfFile(null);
    }

    function offsetNext() {
        setOffset((current) => current + limit);
    }

    function offsetPrev() {
        setOffset((current) => Math.max(0, current - limit));
    }

    if (!canView) {
        return (
            <div>
                <h2>Report List</h2>
                <p role="alert">
                    You are not authorized to view reports.
                </p>
            </div>
        );
    }

    return (
        <div>
            <h2>Report List</h2>

            {loading && <p>Loading reports...</p>}
            {error && <p role="alert">Error: {error}</p>}

            {!loading && !error && reports.length === 0 && (
                <p>No reports found.</p>
            )}

            {!loading && !error && reports.length > 0 && (
                <table>
                    <thead>
                        <tr>
                            <th>Report ID</th>
                            <th>Scan ID</th>
                            <th>Radiologist ID</th>
                            <th>Finalized At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>

                    <tbody>
                        {reports.map((report) => (
                            <tr key={report.id}>
                                <td>{report.id}</td>
                                <td>{report.scan_id}</td>
                                <td>{report.radiologist_id}</td>
                                <td>
                                    {report.finalized_at
                                        ? new Date(
                                            report.finalized_at
                                        ).toLocaleString()
                                        : "Not finalized"}
                                </td>

                                <td>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            handleViewReport(report.id)
                                        }
                                    >
                                        View
                                    </button>{" "}

                                    {canUpdate && (
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleUpdateClick(report.id)
                                            }
                                        >
                                            Update
                                        </button>
                                    )}{" "}

                                    {canDelete && (
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleDeleteReport(report.id)
                                            }
                                        >
                                            Delete
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            <div>
                <button
                    type="button"
                    onClick={offsetPrev}
                    disabled={offset === 0 || loading}
                >
                    Previous
                </button>

                <span>
                    {" "}
                    Page {Math.floor(offset / limit) + 1}
                    {" "}
                </span>

                <button
                    type="button"
                    onClick={offsetNext}
                    disabled={reports.length < limit || loading}
                >
                    Next
                </button>
            </div>

            {modalType && (
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="report-modal-title"
                >
                    <h3 id="report-modal-title">
                        {modalType === "update"
                            ? "Update Report"
                            : "Report Details"}
                    </h3>

                    {modalLoading && <p>Loading report...</p>}

                    {modalError && (
                        <p role="alert">Error: {modalError}</p>
                    )}

                    {modalType === "view" && selectedReport && (
                        <dl>
                            <dt>Report ID</dt>
                            <dd>{selectedReport.id}</dd>

                            <dt>Scan ID</dt>
                            <dd>{selectedReport.scan_id}</dd>

                            <dt>Findings</dt>
                            <dd>{selectedReport.findings}</dd>

                            <dt>Radiologist ID</dt>
                            <dd>{selectedReport.radiologist_id}</dd>

                            <dt>Finalized At</dt>
                            <dd>
                                {selectedReport.finalized_at
                                    ? new Date(
                                        selectedReport.finalized_at
                                    ).toLocaleString()
                                    : "Not finalized"}
                            </dd>

                            <dt>PDF Storage Key</dt>
                            <dd>
                                {selectedReport.pdf_key || "Not available"}
                            </dd>
                        </dl>
                    )}

                    {modalType === "update" &&
                        canUpdate &&
                        selectedReport && (
                            <form onSubmit={handleUpdateReport}>
                                <div>
                                    <label htmlFor="report-scan-id">
                                        Scan ID:
                                    </label>
                                    <input
                                        id="report-scan-id"
                                        value={form.scan_id}
                                        onChange={(event) =>
                                            setForm({
                                                ...form,
                                                scan_id: event.target.value,
                                            })
                                        }
                                        required
                                    />
                                </div>

                                <div>
                                    <label htmlFor="report-findings">
                                        Findings:
                                    </label>
                                    <textarea
                                        id="report-findings"
                                        value={form.findings}
                                        onChange={(event) =>
                                            setForm({
                                                ...form,
                                                findings: event.target.value,
                                            })
                                        }
                                        required
                                    />
                                </div>

                                <div>
                                    <label htmlFor="report-radiologist-id">
                                        Radiologist ID:
                                    </label>
                                    <input
                                        id="report-radiologist-id"
                                        value={form.radiologist_id}
                                        onChange={(event) =>
                                            setForm({
                                                ...form,
                                                radiologist_id:
                                                    event.target.value,
                                            })
                                        }
                                        required
                                    />
                                </div>

                                <div>
                                    <label htmlFor="report-finalized-at">
                                        Finalized At:
                                    </label>
                                    <input
                                        id="report-finalized-at"
                                        type="datetime-local"
                                        value={form.finalized_at}
                                        onChange={(event) =>
                                            setForm({
                                                ...form,
                                                finalized_at:
                                                    event.target.value,
                                            })
                                        }
                                    />
                                </div>

                                <div>
                                    <label htmlFor="report-pdf-file">
                                        Replacement PDF:
                                    </label>
                                    <input
                                        id="report-pdf-file"
                                        type="file"
                                        accept="application/pdf,.pdf"
                                        onChange={(event) =>
                                            setPdfFile(
                                                event.target.files?.[0] ?? null
                                            )
                                        }
                                        required
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={saving || modalLoading}
                                >
                                    {saving ? "Updating..." : "Save Changes"}
                                </button>
                            </form>
                        )}

                    <button
                        type="button"
                        onClick={closeModal}
                        disabled={saving}
                    >
                        Close
                    </button>
                </div>
            )}
        </div>
    );
}
