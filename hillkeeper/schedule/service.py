"""Schedule business logic."""
import datetime
import logging

from ..config import (
    KST,
    DAY_NAMES_REVERSE,
    DEFAULT_MEETING_HOUR,
    DEFAULT_MEETING_INTERVAL_DAYS,
    DEFAULT_MEETING_MINUTE,
    DEFAULT_MEETING_START_DATE,
)
from . import repository

logger = logging.getLogger('hillkeeper')


def is_regular_meeting_date(date: datetime.date) -> bool:
    """Return whether a date belongs to the biweekly meeting cadence."""
    days_since_start = (date - DEFAULT_MEETING_START_DATE).days
    return days_since_start >= 0 and days_since_start % DEFAULT_MEETING_INTERVAL_DAYS == 0


async def get_effective_schedule_for_date(
    date: datetime.date,
) -> tuple[int, int] | None:
    """Return the meeting time for a date unless it is off-cycle or skipped."""
    if not is_regular_meeting_date(date):
        return None

    override = await repository.get_override(str(date))
    if override is not None and override.is_skip:
        return None

    return DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE


async def get_next_meeting(
    *, from_datetime: datetime.datetime | None = None,
) -> dict:
    """Return the next non-skipped meeting at or after a point in time."""
    now = from_datetime or datetime.datetime.now(KST)

    if now.date() <= DEFAULT_MEETING_START_DATE:
        candidate = DEFAULT_MEETING_START_DATE
    else:
        elapsed_days = (now.date() - DEFAULT_MEETING_START_DATE).days
        completed_intervals = elapsed_days // DEFAULT_MEETING_INTERVAL_DAYS
        candidate = DEFAULT_MEETING_START_DATE + datetime.timedelta(
            days=completed_intervals * DEFAULT_MEETING_INTERVAL_DAYS
        )

    meeting_time = datetime.time(
        hour=DEFAULT_MEETING_HOUR,
        minute=DEFAULT_MEETING_MINUTE,
        tzinfo=KST,
    )
    candidate_at = datetime.datetime.combine(candidate, meeting_time)
    if candidate_at < now:
        candidate += datetime.timedelta(days=DEFAULT_MEETING_INTERVAL_DAYS)

    while True:
        override = await repository.get_override(str(candidate))
        if override is None or not override.is_skip:
            break
        candidate += datetime.timedelta(days=DEFAULT_MEETING_INTERVAL_DAYS)

    return {
        "date": candidate,
        "weekday": candidate.weekday(),
        "day_name": DAY_NAMES_REVERSE[candidate.weekday()],
        "hour": DEFAULT_MEETING_HOUR,
        "minute": DEFAULT_MEETING_MINUTE,
    }


async def skip_next_meeting(*, user_id: int) -> dict:
    """Cancel the next non-skipped meeting and return its schedule."""
    meeting = await get_next_meeting()
    date = str(meeting["date"])

    await repository.save_override(
        date=date,
        hour=None,
        minute=None,
        is_skip=True,
        created_by=user_id,
    )

    logger.info(f"Schedule skip: {date} by user {user_id}")
    return meeting
