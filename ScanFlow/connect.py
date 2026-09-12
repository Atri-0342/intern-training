import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("DB_PASSWORD")

if not password:
    raise RuntimeError("DB_PASSWORD was not loaded")

with psycopg.connect(
    dbname="scanflow",
    user="postgres",
    password=password,
) as conn:
    print("Connected successfully")

    with conn.cursor() as cur:
        cur.execute("select count(*) from scans")
        res=cur.fetchone()
        print("total scans: ",res[0])