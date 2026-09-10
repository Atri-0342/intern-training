import time
import os
import psycopg


conn = psycopg.connect(
    dbname="scanflow",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost",
    port="5432",
)

cur = conn.cursor()

cur.execute("""
    SELECT synthetic_study_id
    FROM patients
    LIMIT 100
""")

patients = cur.fetchall()

start = time.perf_counter()

for (patient_id) in patients:
    cur.execute("""
        SELECT COUNT(*)
        FROM scans
        WHERE patient_id = %s
    """, (patient_id))
    cur.fetchone()

elapsed = time.perf_counter() - start

print(f"N+1 queries: {len(patients) + 1}")
print(f"N+1 time: {elapsed:.6f} seconds")

cur.close()
conn.close()