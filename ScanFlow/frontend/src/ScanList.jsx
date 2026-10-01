import react from 'react';
import { useState, useEffect } from 'react';
import {apiFetch} from './api';
import {ScanDetail} from './ScanDetail';


export function ScanList() {
    const [scans, setScans] = useState([]);
    const [modality, setModality] = useState('');
    const [status, setStatus] = useState('');
    const [limit] = useState(10);
    const [offset, setOffset] = useState(0);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [selectedScanId, setSelectedScanId] = useState(null);
    const [showScanDetail, setShowScanDetail] = useState(false);


    useEffect(() => {
        load_scans();
    }, [modality, status, limit, offset]);


    async function load_scans() {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams();

            params.set('limit', limit);
            params.set('offset', offset);

            if (modality) {
                params.set('modality', modality);
            }

            if (status) {
                params.set('status', status);
            }

            const data = await apiFetch(
                `/v1/scans?${params.toString()}`
            );

            setScans(data.items || data);

        } catch (err) {
            setError(err.message);

        } finally {
            setLoading(false);
        }
    }


    function handleScanClick(scanId) {
        setSelectedScanId(scanId);
        setShowScanDetail(true);
    }


    function closeScanDetail() {
        setShowScanDetail(false);
        setSelectedScanId(null);
    }


    function offestNext() {
        setOffset(offset + limit);
    }


    function offsetPrev() {
        setOffset(Math.max(0, offset - limit));
    }


    return (
        <div>
            <h2>Scan List</h2>

            <div>
                <label>
                    Modality:

                    <select
                        value={modality}
                        onChange={(event) => {
                            setModality(event.target.value);
                            setOffset(0);
                        }}
                    >
                        <option value="">All</option>
                        <option value="CT">CT</option>
                        <option value="MRI">MRI</option>
                        <option value="X-ray">X-ray</option>
                    </select>
                </label>


                <label>
                    Status:

                    <select
                        value={status}
                        onChange={(event) => {
                            setStatus(event.target.value);
                            setOffset(0);
                        }}
                    >
                        <option value="">All</option>
                        <option value="uploaded">Uploaded</option>
                        <option value="processing">Processing</option>
                        <option value="completed">Completed</option>
                        <option value="failed">Failed</option>
                    </select>
                </label>
            </div>


            {loading && <p>Loading...</p>}

            {error && <p>Error: {error}</p>}


            {!loading && !error && scans.length === 0 && (
                <p>No scans found.</p>
            )}


            {!loading && !error && scans.length > 0 && (
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Patient ID</th>
                            <th>Modality</th>
                            <th>Body Part</th>
                            <th>Acquired At</th>
                            <th>Uploaded At</th>
                            <th>Status</th>
                            <th>Created At</th>
                            <th>Updated At</th>
                            <th>Action</th>
                        </tr>
                    </thead>

                    <tbody>
                        {scans.map((scan) => (
                            <tr key={scan.id}>
                                <td>{scan.id}</td>
                                <td>{scan.patient_id}</td>
                                <td>{scan.modality}</td>
                                <td>{scan.body_part}</td>
                                <td>{scan.acquired_at}</td>
                                <td>
                                    {scan.uploaded_at || 'Not uploaded'}
                                </td>
                                <td>{scan.status}</td>
                                <td>{scan.created_at}</td>
                                <td>{scan.updated_at}</td>

                                <td>
                                    <button
                                        onClick={() =>
                                            handleScanClick(scan.id)
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
                    onClick={offestNext}
                    disabled={scans.length < limit || loading}
                >
                    Next
                </button>
            </div>


            {showScanDetail && selectedScanId && (
                <ScanDetail
                    scanId={selectedScanId}
                />
            )}

            {showScanDetail && (
                <button onClick={closeScanDetail}>
                    Close
                </button>
            )}
        </div>
    );
}