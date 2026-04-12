"""Schedule business logic."""
import logging
from datetime import datetime, timedelta

from ..config import (
    KST, DAY_NAMES_REVERSE,
    DEFAULT_MEETING_WEEKDAY, DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE,
)
from . import repository

logger = logging.getLogger('hillkeeper')


def _validate_time(*, hour: int, minute: int):
    """
    Validate meeting time values.

    Args:
        hour: Hour (0-23).
        minute: Minute (0-59).

    Raises:
        ValueError: If values are out of range.
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"시간은 0~23 사이여야 합니다: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"분은 0~59 사이여야 합니다: {minute}")


def _get_date_for_weekday_this_week(weekday: int) -> str:
    """
    Calculate the date for a given weekday in the current Mon-Sun week.

    Args:
        weekday: Target weekday (0=Monday, 6=Sunday).

    Returns:
        Date string in YYYY-MM-DD format.
    """
    now = datetime.now(KST)
    current_weekday = now.weekday()
    delta = weekday - current_weekday
    target_date = now.date() + timedelta(days=delta)
    return str(target_date)


async def _get_default_weekday() -> int:
    """Return the current default meeting weekday from Redis or fallback."""
    default = await repository.get_default()
    if default is not None:
        return default.weekday
    return DEFAULT_MEETING_WEEKDAY


async def reschedule_once(*, weekday: int, hour: int, minute: int, user_id: int) -> str:
    """
    Schedule a one-time meeting on a different day/time this week.

    If the target day differs from the default, also creates a skip
    override for the original default day.

    Args:
        weekday: Target weekday (0=Monday, 6=Sunday).
        hour: Meeting hour.
        minute: Meeting minute.
        user_id: Discord user ID who made the change.

    Returns:
        Korean notification message string.

    Raises:
        ValueError: If time values are invalid.
    """
    _validate_time(hour=hour, minute=minute)

    target_date = _get_date_for_weekday_this_week(weekday)
    day_name = DAY_NAMES_REVERSE[weekday]

    # If moving to a different day, skip the original default day
    default_weekday = await _get_default_weekday()
    if weekday != default_weekday:
        original_date = _get_date_for_weekday_this_week(default_weekday)
        await repository.save_override(
            date=original_date, hour=None, minute=None,
            is_skip=True, created_by=user_id,
        )

    await repository.save_override(
        date=target_date, hour=hour, minute=minute,
        is_skip=False, created_by=user_id,
    )

    logger.info(f"Schedule once: {day_name} {hour:02d}:{minute:02d} by user {user_id}")
    return f"이번 주 회고 모임 일정이 {day_name} {hour:02d}:{minute:02d}로 변경되었습니다!"


async def reschedule_default(*, weekday: int, hour: int, minute: int, user_id: int) -> str:
    """
    Change the permanent default meeting schedule.

    Args:
        weekday: New default weekday (0=Monday, 6=Sunday).
        hour: Meeting hour.
        minute: Meeting minute.
        user_id: Discord user ID who made the change.

    Returns:
        Korean notification message string.

    Raises:
        ValueError: If time values are invalid.
    """
    _validate_time(hour=hour, minute=minute)

    day_name = DAY_NAMES_REVERSE[weekday]

    await repository.save_default(
        weekday=weekday, hour=hour, minute=minute, updated_by=user_id,
    )

    logger.info(f"Schedule default changed: {day_name} {hour:02d}:{minute:02d} by user {user_id}")
    return f"회고 모임 기본 일정이 {day_name} {hour:02d}:{minute:02d}로 변경되었습니다!"


async def skip_this_week(*, user_id: int) -> str:
    """
    Cancel this week's meeting.

    Determines the meeting day from the default schedule (or hardcoded
    fallback) and creates a skip override.

    Args:
        user_id: Discord user ID who made the change.

    Returns:
        Korean notification message string.
    """
    default_weekday = await _get_default_weekday()
    target_date = _get_date_for_weekday_this_week(default_weekday)

    await repository.save_override(
        date=target_date, hour=None, minute=None,
        is_skip=True, created_by=user_id,
    )

    day_name = DAY_NAMES_REVERSE[default_weekday]
    logger.info(f"Schedule skip: {day_name} ({target_date}) by user {user_id}")
    return f"이번 주 회고 모임({day_name})이 취소되었습니다."


async def get_current_schedule() -> dict:
    """
    Return the current schedule information for display.

    Returns:
        Dict with keys: weekday, hour, minute, day_name, override (optional).
    """
    default = await repository.get_default()

    if default is not None:
        weekday = default.weekday
        hour = default.hour
        minute = default.minute
    else:
        weekday = DEFAULT_MEETING_WEEKDAY
        hour = DEFAULT_MEETING_HOUR
        minute = DEFAULT_MEETING_MINUTE

    day_name = DAY_NAMES_REVERSE[weekday]

    result = {
        "weekday": weekday,
        "hour": hour,
        "minute": minute,
        "day_name": day_name,
    }

    # Check for this week's override on the default day
    default_date = _get_date_for_weekday_this_week(weekday)
    override = await repository.get_override(default_date)
    if override is not None:
        result["override"] = override

    return result
