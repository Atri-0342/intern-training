import { useEffect, useState } from "react";
import { apiFetch } from "./api";

export function PatientList() {
    const [patients, setPatients] = useState([]);
    const [limit] = useState(10);
    const [offset, setOffset] = useState(0);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [selectedPatient, setSelectedPatient] = useState(null);
    const [detailsLoading, setDetailsLoading] = useState(false);
    const [detailsError, setDetailsError] = useState(null);
    const [showPatientDetail, setShowPatientDetail] = useState(false);

    useEffect(() => {
        load_patients();
    }, [limit, offset]);

    async function load_patients() {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();

            params.set("limit", limit);
            params.set("offset", offset);

            const data = await apiFetch(
                `/v1/patients?${params.toString()}`
            );

            setPatients(data.items || data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handlePatientClick(patientId) {
        setSelectedPatient(null);
        setDetailsError(null);
        setShowPatientDetail(true);
        setDetailsLoading(true);

        try {
            const patient = await apiFetch(
                `/v1/patients/${patientId}`
            );

            setSelectedPatient(patient);
        } catch (err) {
            setDetailsError(err.message);
        } finally {
            setDetailsLoading(false);
        }
    }

    function closePatientDetail() {
        setShowPatientDetail(false);
        setSelectedPatient(null);
        setDetailsError(null);
        setDetailsLoading(false);
    }

    function offsetNext() {
        setOffset(offset + limit);
    }

    function offsetPrev() {
        setOffset(Math.max(0, offset - limit));
    }

    return (
        <div>
            <h2>Patient List</h2>

            <div>
                <label>
                    Patients per page:{" "}

                    <select
                        value={limit}
                        onChange={(event) => {
                            // Page size is fixed at 10 in this version.
                            // Change the state declaration if you want
                            // selectable page sizes.
                        }}
                    >
                        <option value={10}>10</option>
                    </select>
                </label>
            </div>

            {loading && <p>Loading patients...</p>}

            {error && <p role="alert">Error: {error}</p>}

            {!loading && !error && patients.length === 0 && (
                <p>No patients found.</p>
            )}

            {!loading && !error && patients.length > 0 && (
                <table>
                    <thead>
                        <tr>
                            <th>Study ID</th>
                            <th>Date of Birth</th>
                            <th>Sex</th>
                            <th>Action</th>
                        </tr>
                    </thead>

                    <tbody>
                        {patients.map((patient) => (
                            <tr key={patient.synthetic_study_id}>
                                <td>{patient.synthetic_study_id}</td>
                                <td>{patient.dob}</td>
                                <td>{patient.sex}</td>

                                <td>
                                    <button
                                        onClick={() =>
                                            handlePatientClick(
                                                patient.synthetic_study_id
                                            )
                                        }
                                    >
                                        View
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            <div>
                <button
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
                    onClick={offsetNext}
                    disabled={patients.length < limit || loading}
                >
                    Next
                </button>
            </div>

            {showPatientDetail && (
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="patient-details-title"
                >
                    <h3 id="patient-details-title">
                        Patient Details
                    </h3>

                    {detailsLoading && (
                        <p>Loading patient details...</p>
                    )}

                    {detailsError && (
                        <p role="alert">
                            Error: {detailsError}
                        </p>
                    )}

                    {selectedPatient && (
                        <dl>
                            <dt>Study ID</dt>
                            <dd>
                                {selectedPatient.synthetic_study_id}
                            </dd>

                            <dt>Date of Birth</dt>
                            <dd>{selectedPatient.dob}</dd>

                            <dt>Sex</dt>
                            <dd>{selectedPatient.sex}</dd>
                        </dl>
                    )}

                    <button onClick={closePatientDetail}>
                        Close
                    </button>
                </div>
            )}
        </div>
    );
}
