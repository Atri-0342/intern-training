
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, Request

from app.api.dependencies import get_current_user
from app.services.rate_limiter import allow_request


RATE_LIMIT_SECRET = os.getenv(
    "RATE_LIMIT_SECRET",
    "local-development-only",
)


def _hash_identity(identity: str) -> str:
    return hmac.new(
        RATE_LIMIT_SECRET.encode(),
        identity.encode(),
        hashlib.sha256,
    ).hexdigest()


def enforce_limit(
    identity: str,
    *,
    capacity: int = 10,
    refill_rate: float = 1.0,
    error_message: str = "Rate limit exceeded. Please try again later.",
    retry_after: int = 1,
) -> None:
    """Apply a Redis token-bucket rate limit."""
    allowed = allow_request(
        user_id=identity,
        capacity=capacity,
        refill_rate=refill_rate,
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=error_message,
            headers={"Retry-After": str(retry_after)},
        )


def enforce_auth_rate_limit(
    request: Request,
    email: str,
) -> None:
    """Shared rate limiter for login and registration."""
    normalized_email = email.strip().lower()

    client_ip = (
        request.client.host
        if request.client is not None
        else "unknown"
    )

    identity = _hash_identity(
        f"{normalized_email}:{client_ip}"
    )

    enforce_limit(
        identity=f"auth:{identity}",
        capacity=5,
        refill_rate=1 / 60,
        error_message="Too many authentication attempts. Please try again later.",
        retry_after=60,
    )


def enforce_user_rate_limit(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Rate-limit requests by authenticated user ID."""
    enforce_limit(
        identity=f"user:{current_user['user_id']}",
        capacity=10,
        refill_rate=1.0,
    )

    return current_user
