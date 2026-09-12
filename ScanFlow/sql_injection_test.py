import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")

def vulnerable_test(body_part: str):
    with psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
    ) as conn:
        with conn.cursor() as cur:
            #query = f"""SELECT * FROM injection_test WHERE body_part = '{body_part}';"""
            cur.execute(
            """
            SELECT *
            FROM injection_test
            WHERE body_part = %s;
            """,
            (body_part,),
            )
            return cur.fetchall()

#results = vulnerable_search_scan("Shoulder")
results = vulnerable_test("'; DROP TABLE injection_test; --")

print(results)