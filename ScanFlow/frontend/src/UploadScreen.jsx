import { useState } from "react";
import { apiFetch } from "./api";

const MAX_FILE_SIZE = 20 * 1024 * 1024;

const ALLOWED_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
];

export function UploadScreen() {
    const [file, setFile] = useState(null);
    const [patientId, setPatientId] = useState("");
    const [modality, setModality] = useState("CT");
    const [bodyPart, setBodyPart] = useState("");
    const [acquiredAt, setAcquiredAt] = useState("");
    const [error, setError] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [success, setSuccess] = useState(null);

    function handleFileChange(event) {
        const selectedFile = event.target.files[0];

        if (!selectedFile) {
            return;
        }

        setError(null);
        setSuccess(null);

        if (!ALLOWED_TYPES.includes(selectedFile.type)) {
            setFile(null);
            setError(
                "Only PDF, JPG, and PNG files are allowed."
            );
            return;
        }

        if (selectedFile.size > MAX_FILE_SIZE) {
            setFile(null);
            setError(
                "File size must be 20 MB or less."
            );
            return;
        }

        setFile(selectedFile);
    }

    async function handleUpload(event) {
        event.preventDefault();

        setError(null);
        setSuccess(null);

        if (!patientId) {
            setError("Patient ID is required.");
            return;
        }

        if (!bodyPart) {
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

            formData.append("patient_id", patientId);
            formData.append("modality", modality);
            formData.append("body_part", bodyPart);
            formData.append("acquired_at", acquiredAt);
            formData.append("file", file);

            const data = await apiFetch(
                "/v1/scans/upload",
                {
                    method: "POST",
                    body: formData,
                }
            );

            setSuccess(
                `Scan uploaded successfully. Scan ID: ${data.id}`
            );

            setFile(null);
            setPatientId("");
            setBodyPart("");
            setAcquiredAt("");
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    }

    return (
        <div>
            <h2>Upload Scan</h2>

            <form onSubmit={handleUpload}>
                <div>
                    <label>
                        Patient ID
                    </label>

                    <input
                        type="text"
                        value={patientId}
                        onChange={(event) =>
                            setPatientId(event.target.value)
                        }
                    />
                </div>

                <div>
                    <label>
                        Modality
                    </label>

                    <select
                        value={modality}
                        onChange={(event) =>
                            setModality(event.target.value)
                        }
                    >
                        <option value="CT">CT</option>
                        <option value="MRI">MRI</option>
                        <option value="X-ray">X-ray</option>
                    </select>
                </div>

                <div>
                    <label>
                        Body Part
                    </label>

                    <input
                        type="text"
                        value={bodyPart}
                        onChange={(event) =>
                            setBodyPart(event.target.value)
                        }
                    />
                </div>

                <div>
                    <label>
                        Acquired At
                    </label>

                    <input
                        type="datetime-local"
                        value={acquiredAt}
                        onChange={(event) =>
                            setAcquiredAt(event.target.value)
                        }
                    />
                </div>

                <div>
                    <label>
                        Scan File
                    </label>

                    <input
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={handleFileChange}
                    />
                </div>

                {file && (
                    <p>
                        Selected file: {file.name}
                    </p>
                )}

                {error && (
                    <p role="alert">
                        {error}
                    </p>
                )}

                {success && (
                    <p>
                        {success}
                    </p>
                )}

                <button
                    type="submit"
                    disabled={uploading}
                >
                    {uploading
                        ? "Uploading..."
                        : "Upload Scan"}
                </button>
            </form>
        </div>
    );
}