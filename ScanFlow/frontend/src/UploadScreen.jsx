
import { useState } from "react";
import { apiFetch } from "./api";

const MAX_FILE_SIZE = 20 * 1024 * 1024;

const ALLOWED_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
];

export function UploadScreen({ role }) {
    const [file, setFile] = useState(null);
    const [patientId, setPatientId] = useState("");
    const [modality, setModality] = useState("CT");
    const [bodyPart, setBodyPart] = useState("");
    const [acquiredAt, setAcquiredAt] = useState("");
    const [error, setError] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState(null);

    const canUpload = role === "clinician";

    function handleFileChange(event) {
        const selectedFile = event.target.files?.[0];

        setError(null);
        setSuccess(null);

        if (!selectedFile) {
            setFile(null);
            return;
        }

        if (!ALLOWED_TYPES.includes(selectedFile.type)) {
            setFile(null);
            event.target.value = "";
            setError("Only PDF, JPG, and PNG files are allowed.");
            return;
        }

        if (selectedFile.size > MAX_FILE_SIZE) {
            setFile(null);
            event.target.value = "";
            setError("File size must be 20 MB or less.");
            return;
        }

        setFile(selectedFile);
    }

    async function handleUpload(event) {
        event.preventDefault();
        setError(null);
        setSuccess(null);

        if (!canUpload) {
            setError("Only clinicians can upload scans.");
            return;
        }

        if (!patientId.trim()) {
            setError("Patient ID is required.");
            return;
        }

        if (!bodyPart.trim()) {
            setError("Body part is required.");
            return;
        }

        if (!acquiredAt) {
            setError("Acquired date and time are required.");
            return;
        }

        if (!file) {
            setError("Please select a scan file.");
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();

            formData.append("patient_id", patientId.trim());
            formData.append("modality", modality);
            formData.append("body_part", bodyPart.trim());

            // datetime-local has no timezone. Convert it to ISO 8601.
            formData.append(
                "acquired_at",
                new Date(acquiredAt).toISOString()
            );

            formData.append("file", file);

            const data = await apiFetch("/v1/scans/", {
                method: "POST",
                headers: {
                    "Idempotency-Key": crypto.randomUUID(),
                },
                body: formData,
            });

            setSuccess(`Scan uploaded successfully. Scan ID: ${data.id}`);
            setFile(null);
            setPatientId("");
            setModality("CT");
            setBodyPart("");
            setAcquiredAt("");
            event.target.reset();
        } catch (err) {
            setError(err.message || "Failed to upload scan.");
        } finally {
            setUploading(false);
        }
    }

    if (!canUpload) {
        return (
            <div>
                <h2>Upload Scan</h2>
                <p>
                    Scan uploads are available to clinicians only.
                    Your current role is: {role || "unknown"}.
                </p>
            </div>
        );
    }

    return (
        <div>
            <h2>Upload Scan</h2>

            <form onSubmit={handleUpload}>
                <div>
                    <label htmlFor="patientId">Patient ID:</label>
                    <input
                        id="patientId"
                        type="text"
                        value={patientId}
                        onChange={(event) => setPatientId(event.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="modality">Modality:</label>
                    <select
                        id="modality"
                        value={modality}
                        onChange={(event) => setModality(event.target.value)}
                        required
                    >
                        <option value="CT">CT</option>
                        <option value="MRI">MRI</option>
                        <option value="X-ray">X-ray</option>
                    </select>
                </div>

                <div>
                    <label htmlFor="bodyPart">Body Part:</label>
                    <input
                        id="bodyPart"
                        type="text"
                        value={bodyPart}
                        onChange={(event) => setBodyPart(event.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="acquiredAt">Acquired At:</label>
                    <input
                        id="acquiredAt"
                        type="datetime-local"
                        value={acquiredAt}
                        onChange={(event) => setAcquiredAt(event.target.value)}
                        required
                    />
                </div>

                <div>
                    <label htmlFor="scanFile">Scan File:</label>
                    <input
                        id="scanFile"
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={handleFileChange}
                        required
                    />
                </div>

                {file && <p>Selected file: {file.name}</p>}

                {error && <p role="alert">{error}</p>}
                {success && <p role="status">{success}</p>}

                <button type="submit" disabled={uploading}>
                    {uploading ? "Uploading..." : "Upload Scan"}
                </button>
            </form>
        </div>
    );
}
