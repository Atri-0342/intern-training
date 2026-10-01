import os
import time

import psycopg
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()

password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")

def normal_test():
    start = time.perf_counter()

    for _ in range(50):
        with psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()

    return time.perf_counter() - start

def pool_test():
    start = time.perf_counter()

    with ConnectionPool(
        conninfo=f"dbname={dbname} user={user} password={password}",
        min_size=5,
        max_size=5,
    ) as pool:

        for _ in range(50):
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()

    return time.perf_counter() - start

normal_time = normal_test()
pool_time = pool_test()

print(f"Normal connections: {normal_time:.4f} seconds")
print(f"Pool connections: {pool_time:.4f} seconds")
