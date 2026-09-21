import asyncio

from fastapi import FastAPI

app = FastAPI()


@app.get("/sleep")
async def sleep_endpoint() -> dict:
    await asyncio.sleep(0.2)

    return {
        "slept": 0.2,
    }