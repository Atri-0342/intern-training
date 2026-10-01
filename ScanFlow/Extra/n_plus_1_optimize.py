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

start = time.perf_counter()

cur.execute("""
    SELECT
        p.synthetic_study_id,
        COUNT(s.id) AS scan_count
    FROM patients p
    LEFT JOIN scans s
        ON s.patient_id = p.synthetic_study_id
    GROUP BY p.synthetic_study_id
    LIMIT 100
""")

results = cur.fetchall()

elapsed = time.perf_counter() - start

print(f"Single JOIN query: 1")
print(f"Rows returned: {len(results)}")
print(f"JOIN time: {elapsed:.6f} seconds")

cur.close()
conn.close()