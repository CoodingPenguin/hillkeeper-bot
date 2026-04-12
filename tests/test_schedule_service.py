"""Tests for schedule/service.py."""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST, DEFAULT_MEETING_WEEKDAY
from hillkeeper.schedule import service
from hillkeeper.schedule.repository import DefaultSchedule, ScheduleOverride


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
FIXED_DATE = FIXED_THURSDAY.date()

# 2026-04-06 is Monday, 2026-04-12 is Sunday (same week)
MONDAY_OF_WEEK = datetime.date(2026, 4, 6)
SUNDAY_OF_WEEK = datetime.date(2026, 4, 12)


@pytest.fixture(autouse=True)
def patch_datetime():
    """Patch datetime.now to a fixed Thursday."""
    with patch("hillkeeper.schedule.service.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_THURSDAY
        mock_dt.date = datetime.date
        mock_dt.timedelta = datetime.timedelta
        yield mock_dt


@pytest.fixture
def mock_repo():
    """Mock the schedule repository module."""
    with patch("hillkeeper.schedule.service.repository") as mock:
        mock.save_default = AsyncMock()
        mock.get_default = AsyncMock(return_value=None)
        mock.save_override = AsyncMock()
        mock.get_override = AsyncMock(return_value=None)
        mock.delete_override = AsyncMock()
        mock.TTL_7_DAYS = 604800
        yield mock


# --- reschedule_once ---

class TestRescheduleOnce:

    async def test_saves_override_for_given_weekday(self, mock_repo):
        """Selecting Friday saves override for 2026-04-10 (Friday of this week).
        Also skips the default Thursday since target is a different day."""
        result = await service.reschedule_once(weekday=4, hour=22, minute=0, user_id=123)
        # Called twice: skip Thursday + reschedule Friday
        assert mock_repo.save_override.call_count == 2
        # Last call is the actual reschedule
        call_kwargs = mock_repo.save_override.call_args_list[1][1]
        assert call_kwargs["date"] == "2026-04-10"
        assert call_kwargs["hour"] == 22
        assert call_kwargs["minute"] == 0
        assert call_kwargs["is_skip"] is False
        assert call_kwargs["created_by"] == 123

    async def test_returns_notification_message(self, mock_repo):
        result = await service.reschedule_once(weekday=4, hour=22, minute=0, user_id=123)
        assert "금요일" in result
        assert "22:00" in result

    async def test_also_skips_original_meeting_day(self, mock_repo):
        """When moving to a different day, also skip the original default day."""
        mock_repo.get_default.return_value = DefaultSchedule(
            weekday=3, hour=22, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        await service.reschedule_once(weekday=4, hour=22, minute=0, user_id=123)
        # Should save two overrides: skip for Thursday + reschedule for Friday
        assert mock_repo.save_override.call_count == 2

    async def test_same_day_override_saves_only_one(self, mock_repo):
        """When rescheduling to the same day (just different time), only one override."""
        mock_repo.get_default.return_value = DefaultSchedule(
            weekday=3, hour=22, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        # Reschedule to Thursday (same day) but different time
        await service.reschedule_once(weekday=3, hour=21, minute=0, user_id=123)
        assert mock_repo.save_override.call_count == 1

    async def test_rejects_invalid_hour(self, mock_repo):
        with pytest.raises(ValueError, match="시간"):
            await service.reschedule_once(weekday=4, hour=25, minute=0, user_id=123)

    async def test_rejects_invalid_minute(self, mock_repo):
        with pytest.raises(ValueError, match="분"):
            await service.reschedule_once(weekday=4, hour=22, minute=60, user_id=123)


# --- reschedule_default ---

class TestRescheduleDefault:

    async def test_saves_default_schedule(self, mock_repo):
        result = await service.reschedule_default(weekday=2, hour=21, minute=0, user_id=123)
        mock_repo.save_default.assert_called_once()
        call_kwargs = mock_repo.save_default.call_args[1]
        assert call_kwargs["weekday"] == 2
        assert call_kwargs["hour"] == 21
        assert call_kwargs["minute"] == 0
        assert call_kwargs["updated_by"] == 123

    async def test_returns_notification_message(self, mock_repo):
        result = await service.reschedule_default(weekday=2, hour=21, minute=0, user_id=123)
        assert "수요일" in result
        assert "21:00" in result

    async def test_rejects_invalid_hour(self, mock_repo):
        with pytest.raises(ValueError, match="시간"):
            await service.reschedule_default(weekday=2, hour=-1, minute=0, user_id=123)

    async def test_rejects_invalid_minute(self, mock_repo):
        with pytest.raises(ValueError, match="분"):
            await service.reschedule_default(weekday=2, hour=21, minute=99, user_id=123)


# --- skip_this_week ---

class TestSkipThisWeek:

    async def test_saves_skip_override_for_default_day(self, mock_repo):
        """Skip uses the default meeting day (Thursday from Redis)."""
        mock_repo.get_default.return_value = DefaultSchedule(
            weekday=3, hour=22, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        result = await service.skip_this_week(user_id=123)
        mock_repo.save_override.assert_called_once()
        call_kwargs = mock_repo.save_override.call_args[1]
        assert call_kwargs["is_skip"] is True
        assert call_kwargs["date"] == "2026-04-09"  # Thursday of this week

    async def test_falls_back_to_hardcoded_thursday(self, mock_repo):
        """When no default in Redis, skip the hardcoded Thursday."""
        mock_repo.get_default.return_value = None
        await service.skip_this_week(user_id=123)
        call_kwargs = mock_repo.save_override.call_args[1]
        assert call_kwargs["date"] == "2026-04-09"  # Thursday

    async def test_returns_notification_message(self, mock_repo):
        mock_repo.get_default.return_value = None
        result = await service.skip_this_week(user_id=123)
        assert "취소" in result

    async def test_also_skips_once_override_if_exists(self, mock_repo):
        """If there's already a once override this week, skip that day too."""
        mock_repo.get_default.return_value = DefaultSchedule(
            weekday=3, hour=22, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        # There's already a once override for Friday
        mock_repo.get_override.return_value = ScheduleOverride(
            date="2026-04-10", hour=22, minute=0, is_skip=False,
            created_by=123, created_at="2026-04-09T09:00:00+09:00",
        )
        await service.skip_this_week(user_id=123)
        # Should skip both Thursday (default) and Friday (once override)
        assert mock_repo.save_override.call_count >= 1


# --- get_current_schedule ---

class TestGetCurrentSchedule:

    async def test_returns_default_from_redis(self, mock_repo):
        mock_repo.get_default.return_value = DefaultSchedule(
            weekday=3, hour=22, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        result = await service.get_current_schedule()
        assert result["weekday"] == 3
        assert result["hour"] == 22
        assert result["minute"] == 0
        assert result["day_name"] == "목요일"

    async def test_returns_hardcoded_fallback(self, mock_repo):
        mock_repo.get_default.return_value = None
        result = await service.get_current_schedule()
        assert result["weekday"] == DEFAULT_MEETING_WEEKDAY
        assert result["day_name"] == "목요일"

    async def test_includes_override_info(self, mock_repo):
        """When an override exists for the default day, include it in result."""
        mock_repo.get_default.return_value = None
        mock_repo.get_override.return_value = ScheduleOverride(
            date="2026-04-09", hour=21, minute=0, is_skip=False,
            created_by=123, created_at="2026-04-09T09:00:00+09:00",
        )
        result = await service.get_current_schedule()
        assert "override" in result
        assert result["override"].hour == 21
