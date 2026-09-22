import asyncio
import time


def blocking_work() -> str:
    time.sleep(2)
    return "done"

async def bad_task(name: str) -> str:
    print(f"{name} started")
    blocking_work()
    print(f"{name} finished")
    return "done"

async def bad_blocking_test() -> float:
    start = time.perf_counter()

    task1 = asyncio.create_task(bad_task("Task 1"))
    task2 = asyncio.create_task(bad_task("Task 2"))

    results = await asyncio.gather(task1, task2)

    elapsed = time.perf_counter() - start

    print(f"Results: {results}")
    print(f"Blocking version: {elapsed:.3f} seconds")

    return elapsed

async def good_task(name: str) -> str:
    print(f"{name} started")

    result = await asyncio.to_thread(blocking_work)

    print(f"{name} finished")
    return result


async def fixed_blocking_test() -> float:
    start = time.perf_counter()

    task1 = asyncio.create_task(good_task("Task 1"))
    task2 = asyncio.create_task(good_task("Task 2"))

    results = await asyncio.gather(task1, task2)

    elapsed = time.perf_counter() - start

    print(f"Results: {results}")
    print(f"Fixed version: {elapsed:.3f} seconds")

    return elapsed

if __name__ == "__main__":
    asyncio.run(bad_blocking_test())
    asyncio.run(fixed_blocking_test())