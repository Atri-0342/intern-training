import time

import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
import aiohttp
import httpx

URL = "http://127.0.0.1:8000/sleep"
REQUEST_COUNT = 50


def sequential_io() -> float:
    start = time.perf_counter()

    for _ in range(REQUEST_COUNT):
        response = requests.get(URL)
        response.raise_for_status()

    elapsed = time.perf_counter() - start
    return elapsed

def threaded_io() -> float:
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(requests.get, URL)for _ in range(REQUEST_COUNT)]

        for future in futures:
            response = future.result()
            response.raise_for_status()

    elapsed = time.perf_counter() - start
    return elapsed

from concurrent.futures import ProcessPoolExecutor


def process_io() -> float:
    start = time.perf_counter()

    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(requests.get, URL)
            for _ in range(REQUEST_COUNT)
        ]

        for future in futures:
            response = future.result()
            response.raise_for_status()

    elapsed = time.perf_counter() - start
    return elapsed

import asyncio

import aiohttp


async def asyncio_io() -> float:
    start = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        tasks = [session.get(URL)for _ in range(REQUEST_COUNT)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            response.raise_for_status()
            await response.read()

    elapsed = time.perf_counter() - start
    return elapsed

async def asyncio_httpx_io() -> float:
    start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(URL)
            for _ in range(REQUEST_COUNT)
        ]

        responses = await asyncio.gather(*tasks)

        for response in responses:
            response.raise_for_status()

    elapsed = time.perf_counter() - start
    return elapsed

PRIME_LIMIT = 2_000_000
CPU_RUNS = 8


def sum_primes(limit: int) -> int:
    total = 0

    for number in range(2, limit):
        is_prime = True

        for divisor in range(2, int(number ** 0.5) + 1):
            if number % divisor == 0:
                is_prime = False
                break

        if is_prime:
            total += number

    return total

def sequential_cpu() -> float:
    start = time.perf_counter()

    for _ in range(CPU_RUNS):
        sum_primes(PRIME_LIMIT)

    elapsed = time.perf_counter() - start
    return elapsed

def threaded_cpu() -> float:
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(sum_primes, PRIME_LIMIT)
            for _ in range(CPU_RUNS)
        ]

        for future in futures:
            future.result()

    elapsed = time.perf_counter() - start
    return elapsed

def process_cpu() -> float:
    start = time.perf_counter()

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(sum_primes, PRIME_LIMIT)
            for _ in range(CPU_RUNS)
        ]

        for future in futures:
            future.result()

    elapsed = time.perf_counter() - start
    return elapsed

async def asyncio_cpu() -> float:
    start = time.perf_counter()

    tasks = [
        asyncio.to_thread(sum_primes, PRIME_LIMIT)
        for _ in range(CPU_RUNS)
    ]

    await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start
    return elapsed

if __name__ == "__main__":
    sequential_elapsed = sequential_io()
    print(f"Sequential I/O: {sequential_elapsed:.3f} seconds")

    threaded_elapsed = threaded_io()
    print(f"Threaded I/O: {threaded_elapsed:.3f} seconds")

    process_elapsed = process_io()
    print(f"Process I/O: {process_elapsed:.3f} seconds")

    asyncio_elapsed = asyncio.run(asyncio_io())
    print(f"Asyncio I/O: {asyncio_elapsed:.3f} seconds")

    result = asyncio.run(asyncio_httpx_io())
    print(f"Asyncio + HTTPX I/O: {result:.3f} seconds")


    