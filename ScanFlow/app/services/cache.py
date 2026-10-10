
from app.core.redis_client import redis_client


def set_cache(
    key: str,
    value: str,
    ttl_seconds: int = 300,
) -> None:
    redis_client.set(
        key,
        value,
        ex=ttl_seconds,
    )


def get_cache(
    key: str,
) -> str | None:
    return redis_client.get(key)


def delete_cache(
    key: str,
) -> None:
    redis_client.delete(key)
