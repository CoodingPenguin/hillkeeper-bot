"""Tests for tasks.py."""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST
from hillkeeper.bot.tasks import _run_scheduled_task, initialize_task_schedule


THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
MONDAY = datetime.datetime(2026, 4, 6, 9, 0, 0, tzinfo=KST)


@pytest.fixture
def mock_schedule_repo():
    """Mock the schedule repository."""
    with patch("hillkeeper.bot.tasks.schedule_repository") as mock:
        mock.get_effective_schedule_for_date = AsyncMock(return_value=None)
        mock.get_default = AsyncMock(return_value=None)
        yield mock


class TestRunScheduledTask:

    async def test_calls_service_when_meeting_scheduled(self, env_vars, mock_schedule_repo):
        """Service is called when get_effective_schedule_for_date returns a time."""
        mock_schedule_repo.get_effective_schedule_for_date.return_value = (22, 0)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_called_once()

    async def test_skips_when_no_meeting(self, env_vars, mock_schedule_repo):
        """Service is not called when get_effective_schedule_for_date returns None."""
        mock_schedule_repo.get_effective_schedule_for_date.return_value = None
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = MONDAY
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_not_called()

    async def test_skips_when_env_vars_missing(self, monkeypatch, mock_schedule_repo):
        """Service is not called when required env vars are missing."""
        monkeypatch.delenv("ATTENDANCE_CHANNEL_ID", raising=False)
        monkeypatch.delenv("RETROSPECTIVE_ROLE_ID", raising=False)
        mock_schedule_repo.get_effective_schedule_for_date.return_value = (22, 0)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_not_called()

    async def test_passes_channel_and_role_to_service(self, env_vars, mock_schedule_repo):
        mock_schedule_repo.get_effective_schedule_for_date.return_value = (22, 0)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_called_once_with(bot, "100", "200")


class TestInitializeTaskSchedule:

    async def test_uses_default_time_when_no_redis_schedule(self, mock_schedule_repo):
        """When no default in Redis, evening reminder keeps its default time."""
        mock_schedule_repo.get_default.return_value = None
        bot = AsyncMock()
        bot.evening_reminder = AsyncMock()
        bot.evening_reminder.change_interval = AsyncMock()
        await initialize_task_schedule(bot)
        # No change_interval call needed — task already uses default 21:45
        bot.evening_reminder.change_interval.assert_not_called()

    async def test_updates_evening_reminder_with_redis_schedule(self, mock_schedule_repo):
        """When Redis has a different default, update evening reminder time."""
        from hillkeeper.schedule.repository import DefaultSchedule
        mock_schedule_repo.get_default.return_value = DefaultSchedule(
            weekday=2, hour=21, minute=0, updated_by=123,
            updated_at="2026-04-09T09:00:00+09:00",
        )
        bot = AsyncMock()
        bot.evening_reminder = AsyncMock()
        bot.evening_reminder.change_interval = AsyncMock()
        await initialize_task_schedule(bot)
        bot.evening_reminder.change_interval.assert_called_once()
        call_kwargs = bot.evening_reminder.change_interval.call_args[1]
        # 21:00 meeting → 20:45 reminder
        assert call_kwargs["time"].hour == 20
        assert call_kwargs["time"].minute == 45
