import asyncio
import time

import httpx


SYNC_URL = "http://127.0.0.1:8000/v1/bench/patients-sync"
ASYNC_URL = "http://127.0.0.1:8000/v1/bench/patients-async"

REQUEST_COUNT = 20


async def benchmark_endpoint(url: str, name: str) -> float:
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()

        tasks = [
            client.get(url)
            for _ in range(REQUEST_COUNT)
        ]

        responses = await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start

        for response in responses:
            response.raise_for_status()

    print(f"{name}: {elapsed:.3f} seconds")

    return elapsed


async def main() -> None:
    print(f"Sending {REQUEST_COUNT} concurrent requests...")

    sync_time = await benchmark_endpoint(
        SYNC_URL,
        "Sync",
    )

    async_time = await benchmark_endpoint(
        ASYNC_URL,
        "Async",
    )

    print()
    print(f"Sync total:  {sync_time:.3f} seconds")
    print(f"Async total: {async_time:.3f} seconds")


if __name__ == "__main__":
    asyncio.run(main())