"""Tests for schedule/service.py."""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST
from hillkeeper.schedule import service
from hillkeeper.schedule.repository import ScheduleOverride


START_AT = datetime.datetime(2026, 7, 7, 9, 0, tzinfo=KST)


@pytest.fixture
def mock_repo():
    """Mock the schedule repository module."""
    with patch("hillkeeper.schedule.service.repository") as mock:
        mock.get_override = AsyncMock(return_value=None)
        mock.save_override = AsyncMock()
        yield mock


class TestIsRegularMeetingDate:

    def test_start_date_is_meeting_date(self):
        assert service.is_regular_meeting_date(datetime.date(2026, 7, 7))

    def test_two_weeks_after_start_is_meeting_date(self):
        assert service.is_regular_meeting_date(datetime.date(2026, 7, 21))

    def test_intervening_tuesday_is_not_meeting_date(self):
        assert not service.is_regular_meeting_date(datetime.date(2026, 7, 14))

    def test_date_before_start_is_not_meeting_date(self):
        assert not service.is_regular_meeting_date(datetime.date(2026, 6, 23))


class TestGetEffectiveScheduleForDate:

    async def test_returns_time_on_regular_meeting_date(self, mock_repo):
        result = await service.get_effective_schedule_for_date(
            datetime.date(2026, 7, 7)
        )
        assert result == (22, 0)

    async def test_returns_none_on_off_week(self, mock_repo):
        result = await service.get_effective_schedule_for_date(
            datetime.date(2026, 7, 14)
        )
        assert result is None
        mock_repo.get_override.assert_not_called()

    async def test_returns_none_when_meeting_is_skipped(self, mock_repo):
        mock_repo.get_override.return_value = ScheduleOverride(
            date="2026-07-07",
            hour=None,
            minute=None,
            is_skip=True,
            created_by=123,
            created_at="2026-06-22T09:00:00+09:00",
        )
        result = await service.get_effective_schedule_for_date(
            datetime.date(2026, 7, 7)
        )
        assert result is None


class TestGetNextMeeting:

    async def test_returns_start_date_before_first_meeting(self, mock_repo):
        result = await service.get_next_meeting(
            from_datetime=datetime.datetime(2026, 6, 22, 12, 0, tzinfo=KST)
        )
        assert result["date"] == datetime.date(2026, 7, 7)
        assert result["day_name"] == "화요일"
        assert result["hour"] == 22

    async def test_returns_today_before_meeting_time(self, mock_repo):
        result = await service.get_next_meeting(from_datetime=START_AT)
        assert result["date"] == datetime.date(2026, 7, 7)

    async def test_returns_next_cycle_after_meeting_time(self, mock_repo):
        result = await service.get_next_meeting(
            from_datetime=datetime.datetime(2026, 7, 7, 22, 1, tzinfo=KST)
        )
        assert result["date"] == datetime.date(2026, 7, 21)

    async def test_skips_cancelled_meeting(self, mock_repo):
        skipped = ScheduleOverride(
            date="2026-07-07",
            hour=None,
            minute=None,
            is_skip=True,
            created_by=123,
            created_at="2026-06-22T09:00:00+09:00",
        )
        mock_repo.get_override.side_effect = [skipped, None]
        result = await service.get_next_meeting(from_datetime=START_AT)
        assert result["date"] == datetime.date(2026, 7, 21)


class TestSkipNextMeeting:

    async def test_saves_skip_for_next_meeting(self, mock_repo):
        with patch.object(
            service,
            "get_next_meeting",
            AsyncMock(return_value={
                "date": datetime.date(2026, 7, 7),
                "weekday": 1,
                "day_name": "화요일",
                "hour": 22,
                "minute": 0,
            }),
        ):
            result = await service.skip_next_meeting(user_id=123)

        assert result["date"] == datetime.date(2026, 7, 7)
        mock_repo.save_override.assert_awaited_once_with(
            date="2026-07-07",
            hour=None,
            minute=None,
            is_skip=True,
            created_by=123,
        )
