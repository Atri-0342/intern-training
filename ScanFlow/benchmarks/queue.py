import asyncio


async def producer(queue: asyncio.Queue):
    for item in range(10):
        await queue.put(item)
        print(f"Produced: {item}")

    # Send one shutdown signal to each consumer.
    for _ in range(3):
        await queue.put(None)


async def consumer(name: str, queue: asyncio.Queue):
    while True:
        item = await queue.get()

        if item is None:
            queue.task_done()
            print(f"{name} shutting down")
            break

        print(f"{name} processing item {item}")

        await asyncio.sleep(0.5)

        print(f"{name} finished item {item}")

        queue.task_done()


async def main():
    queue = asyncio.Queue()

    producer_task = asyncio.create_task(
        producer(queue)
    )

    consumer_tasks = [
        asyncio.create_task(
            consumer(f"Consumer-{i}", queue)
        )
        for i in range(1, 4)
    ]

    await producer_task

    # Wait until every produced item has been processed.
    await queue.join()

    # Wait for all consumers to shut down gracefully.
    await asyncio.gather(*consumer_tasks)


if __name__ == "__main__":
    asyncio.run(main())