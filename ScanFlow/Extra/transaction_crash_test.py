import os
import time

import psycopg
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")

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
            VALUES (
                gen_random_uuid(),
                (
                    SELECT synthetic_study_id
                    FROM patients
                    LIMIT 1
                ),
                'CT',
                'Chest',
                now(),
                'uploaded'
            )
            RETURNING id;
            """
        )
        scan_id = cur.fetchone()[0]
        print("Created scan ID:", scan_id)
        print("Row inserted inside transaction.")
        print("Kill this process now.")
        time.sleep(30)