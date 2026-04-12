"""Schedule data access layer (Redis)."""
import logging
from dataclasses import dataclass
from datetime import datetime

from ..config import KST, DEFAULT_MEETING_WEEKDAY, DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE
from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')

TTL_7_DAYS = 604800  # 7 days


@dataclass(frozen=True, slots=True)
class DefaultSchedule:
    """Immutable representation of the default meeting schedule."""
    weekday: int
    hour: int
    minute: int
    updated_by: int
    updated_at: str


@dataclass(frozen=True, slots=True)
class ScheduleOverride:
    """Immutable representation of a one-time schedule override."""
    date: str
    hour: int | None
    minute: int | None
    is_skip: bool
    created_by: int
    created_at: str


def _default_key() -> str:
    """Build the Redis key for the default schedule."""
    return "schedule:default"


def _override_key(date: str) -> str:
    """Build the Redis key for a schedule override."""
    return f"schedule:override:{date}"


async def save_default(*, weekday: int, hour: int, minute: int, updated_by: int):
    """
    Persist the default meeting schedule to Redis.

    Args:
        weekday: Day of week (0=Monday, 6=Sunday).
        hour: Meeting hour (0-23).
        minute: Meeting minute (0-59).
        updated_by: Discord user ID who made the change.
    """
    now = datetime.now(KST)
    key = _default_key()
    await redis_client.client.hset(
        key,
        mapping={
            "weekday": str(weekday),
            "hour": str(hour),
            "minute": str(minute),
            "updated_by": str(updated_by),
            "updated_at": now.isoformat(),
        }
    )
    logger.info(f"Saved default schedule: weekday={weekday} {hour:02d}:{minute:02d}")


async def get_default() -> DefaultSchedule | None:
    """
    Fetch the default meeting schedule from Redis.

    Returns:
        A DefaultSchedule, or None if not set.
    """
    key = _default_key()
    data = await redis_client.client.hgetall(key)

    if not data:
        return None

    return DefaultSchedule(
        weekday=int(data["weekday"]),
        hour=int(data["hour"]),
        minute=int(data["minute"]),
        updated_by=int(data["updated_by"]),
        updated_at=data["updated_at"],
    )


async def save_override(
    *, date: str, hour: int | None, minute: int | None,
    is_skip: bool, created_by: int, ttl: int = TTL_7_DAYS,
):
    """
    Persist a one-time schedule override to Redis.

    Args:
        date: Target date (YYYY-MM-DD).
        hour: Meeting hour, or None if skipping.
        minute: Meeting minute, or None if skipping.
        is_skip: Whether this is a skip override.
        created_by: Discord user ID who made the change.
        ttl: Expiry in seconds (default: 7 days).
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


async def get_effective_schedule_for_date(date) -> tuple[int, int] | None:
    """
    Determine the effective meeting schedule for a given date.

    Checks in priority order:
    1. Override for the specific date (skip → None, reschedule → time)
    2. Default schedule from Redis (matching weekday → time)
    3. Hardcoded fallback (Thursday 22:00)

    Args:
        date: The date to check.

    Returns:
        (hour, minute) tuple if a meeting is scheduled, None otherwise.
    """
    date_str = str(date)
    weekday = date.weekday()

    # 1. Check override
    override = await get_override(date_str)
    if override is not None:
        if override.is_skip:
            return None
        return (override.hour, override.minute)

    # 2. Check default from Redis
    default = await get_default()
    if default is not None:
        if weekday == default.weekday:
            return (default.hour, default.minute)
        return None

    # 3. Hardcoded fallback
    if weekday == DEFAULT_MEETING_WEEKDAY:
        return (DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE)
    return None
