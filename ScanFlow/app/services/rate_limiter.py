
import time

from app.core.redis_client import redis_client


def allow_request(
    user_id: str,
    capacity: int = 10,
    refill_rate: float = 1.0,
) -> bool:
    key = f"rate-limit:{user_id}"

    now = time.time()

    bucket = redis_client.hgetall(key)

    if bucket:
        tokens = float(bucket["tokens"])
        last_refill = float(bucket["last_refill"])
    else:
        tokens = float(capacity)
        last_refill = now

    elapsed = max(0.0, now - last_refill)
    tokens = min(capacity, tokens + elapsed * refill_rate)

    if tokens < 1:
        redis_client.hset(
            key,
            mapping={
                "tokens": tokens,
                "last_refill": now,
            },
        )
        redis_client.expire(key, 3600)
        return False

    tokens -= 1

    redis_client.hset(
        key,
        mapping={
            "tokens": tokens,
            "last_refill": now,
        },
    )
    redis_client.expire(key, 3600)

    return True
