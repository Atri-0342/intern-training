import asyncio
import random


async def flaky_call() -> str:
    delay = random.uniform(0.1, 1.5)

    print(f"Flaky call will take {delay:.2f}s")

    await asyncio.sleep(delay)

    if random.random() < 0.5:
        raise RuntimeError("Temporary failure")

    return "success"


async def call_with_retry(
    max_attempts: int = 3,
    timeout_seconds: float = 1.0,
) -> str:

    delay = 0.5

    for attempt in range(1, max_attempts + 1):

        try:
            print(f"\nAttempt {attempt}")

            async with asyncio.timeout(timeout_seconds):
                result = await flaky_call()

            print(f"Attempt {attempt} succeeded")

            return result

        except (TimeoutError, RuntimeError) as exc:

            print(f"Attempt {attempt} failed: {exc}")

            if attempt == max_attempts:
                print("No attempts remaining")
                raise

            print(f"Retrying in {delay:.1f}s...")

            await asyncio.sleep(delay)

            delay *= 2


async def main():

    try:
        result = await call_with_retry(
            max_attempts=3,
            timeout_seconds=1.0,
        )

        print(f"\nFinal result: {result}")

    except Exception as exc:
        print(f"\nFinal failure: {exc}")


if __name__ == "__main__":
    asyncio.run(main())