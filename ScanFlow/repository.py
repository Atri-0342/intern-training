import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")


def create_scan_table():
    with psycopg.connect(
    dbname=dbname,
    user=user,
    password=password,
    ) as conn:
          with conn.cursor() as cur:
              cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
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
                """
            )
              
def create_scan(
    scan_id: str,
    patient_id: str,
    modality: str,
    body_part: str,
    acquired_at,
    status: str,
) -> tuple:
    with psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO scans (
                    id,
                    patient_id,
                    modality,
                    body_part,
                    acquired_at,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (
                    scan_id,
                    patient_id,
                    modality,
                    body_part,
                    acquired_at,
                    status,
                ),
            )

            return cur.fetchone()

def get_scan(scan_id: str) -> tuple | None:
    with psycopg.connect(
        dbname="scanflow",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM scans
                WHERE id = %s;
                """,
                (scan_id,),
            )

            return cur.fetchone()

def list_scans(
    filters: dict | None,
    limit: int = 100,
    offset: int = 0,
) -> list[tuple]:
    conditions = []
    values = []

    if filters:
        if "patient_id" in filters:
            conditions.append("patient_id = %s")
            values.append(filters["patient_id"])

        if "modality" in filters:
            conditions.append("modality = %s")
            values.append(filters["modality"])

        if "status" in filters:
            conditions.append("status = %s")
            values.append(filters["status"])

        if "body_part" in filters:
            conditions.append("body_part = %s")
            values.append(filters["body_part"])

    query = """
        SELECT *
        FROM scans
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        ORDER BY acquired_at DESC
        LIMIT %s
        OFFSET %s;
    """

    values.extend([limit, offset])

    with psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            return cur.fetchall()

def attach_report(
    report_id: str,
    scan_id: str,
    findings: str,
    radiologist_id: str,
    finalized_at=None,
) -> tuple:
    with psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reports (
                    id,
                    scan_id,
                    findings,
                    radiologist_id,
                    finalized_at
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (
                    report_id,
                    scan_id,
                    findings,
                    radiologist_id,
                    finalized_at,
                ),
            )

            return cur.fetchone()

def claim_next_pending_scan() -> tuple | None:
    with psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH next_scan AS (
                    SELECT id
                    FROM scans
                    WHERE status = 'uploaded'
                    ORDER BY acquired_at, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE scans
                SET status = 'processing',
                    updated_at = now()
                FROM next_scan
                WHERE scans.id = next_scan.id
                RETURNING scans.*;
                """
            )

            return cur.fetchone()
