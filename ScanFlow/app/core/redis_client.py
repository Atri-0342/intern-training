
import os

import redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)
