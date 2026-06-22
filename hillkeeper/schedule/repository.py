"""Schedule data access layer (Redis)."""
import logging
from dataclasses import dataclass
from datetime import datetime

from ..config import KST
from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')

TTL_30_DAYS = 2592000  # 30 days


@dataclass(frozen=True, slots=True)
class ScheduleOverride:
    """Immutable representation of a one-time schedule override."""
    date: str
    hour: int | None
    minute: int | None
    is_skip: bool
    created_by: int
    created_at: str


def _override_key(date: str) -> str:
    """Build the Redis key for a schedule override."""
    return f"schedule:override:{date}"


async def save_override(
    *, date: str, hour: int | None, minute: int | None,
    is_skip: bool, created_by: int, ttl: int = TTL_30_DAYS,
):
    """
    Persist a one-time schedule override to Redis.

    Args:
        date: Target date (YYYY-MM-DD).
        hour: Meeting hour, or None if skipping.
        minute: Meeting minute, or None if skipping.
        is_skip: Whether this is a skip override.
        created_by: Discord user ID who made the change.
        ttl: Expiry in seconds (default: 30 days).
    """
    now = datetime.now(KST)
    key = _override_key(date)
    await redis_client.client.hset(
        key,
        mapping={
            "date": date,
            "hour": str(hour) if hour is not None else "",
            "minute": str(minute) if minute is not None else "",
            "is_skip": str(is_skip).lower(),
            "created_by": str(created_by),
            "created_at": now.isoformat(),
        }
    )
    await redis_client.client.expire(key, ttl)
    logger.info(f"Saved schedule override: {date} skip={is_skip} (ttl={ttl}s)")


async def get_override(date: str) -> ScheduleOverride | None:
    """
    Fetch a schedule override by date.

    Args:
        date: Target date (YYYY-MM-DD).

    Returns:
        A ScheduleOverride, or None if not found.
    """
    key = _override_key(date)
    data = await redis_client.client.hgetall(key)

    if not data:
        return None

    return ScheduleOverride(
        date=data["date"],
        hour=int(data["hour"]) if data["hour"] else None,
        minute=int(data["minute"]) if data["minute"] else None,
        is_skip=data["is_skip"] == "true",
        created_by=int(data["created_by"]),
        created_at=data["created_at"],
    )


async def delete_override(date: str):
    """
    Delete a schedule override from Redis.

    Args:
        date: Target date (YYYY-MM-DD).
    """
    key = _override_key(date)
    await redis_client.client.delete(key)
    logger.info(f"Deleted schedule override: {date}")
