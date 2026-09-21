import time

import requests


URL = "http://127.0.0.1:8000/sleep"
REQUEST_COUNT = 50


def sequential_io() -> float:
    start = time.perf_counter()

    for _ in range(REQUEST_COUNT):
        response = requests.get(URL)
        response.raise_for_status()

    elapsed = time.perf_counter() - start
    return elapsed

elapsed = sequential_io()
print(f"Sequential I/O: {elapsed:.3f} seconds")