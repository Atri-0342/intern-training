CREATE TABLE patients (
    synthetic_study_id uuid PRIMARY KEY,
    dob date NOT NULL,
    sex text NOT NULL CHECK (sex IN ('male', 'female', 'other')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE scans (
    id uuid PRIMARY KEY,
    patient_id uuid NOT NULL REFERENCES patients(synthetic_study_id) ON DELETE RESTRICT,
    modality text NOT NULL CHECK (modality IN ('CT', 'MRI', 'X-ray')),
    body_part text NOT NULL,
    acquired_at timestamptz NOT NULL,
    uploaded_at timestamptz,
    status text NOT NULL CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id uuid PRIMARY KEY,
    email text UNIQUE NOT NULL,
    hashed_password text NOT NULL,
    role text NOT NULL CHECK (role IN ('clinician', 'radiologist', 'admin')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reports (
    id uuid PRIMARY KEY,
    scan_id uuid NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    findings text NOT NULL,
    radiologist_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    finalized_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
    id uuid PRIMARY KEY,
    actor_id uuid REFERENCES users(id) ON DELETE SET NULL,
    action text NOT NULL,
    entity text NOT NULL,
    entity_id text NOT NULL,
    at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);