"""Tests for tasks.py."""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.bot.tasks import _run_scheduled_task
from hillkeeper.config import KST


MEETING_DAY = datetime.datetime(2026, 7, 7, 9, 0, tzinfo=KST)
OFF_WEEK = datetime.datetime(2026, 7, 14, 9, 0, tzinfo=KST)


@pytest.fixture
def mock_schedule_service():
    """Mock the schedule service."""
    with patch("hillkeeper.bot.tasks.schedule_service") as mock:
        mock.get_effective_schedule_for_date = AsyncMock(return_value=None)
        yield mock


class TestRunScheduledTask:

    async def test_calls_service_when_meeting_scheduled(
        self, env_vars, mock_schedule_service
    ):
        mock_schedule_service.get_effective_schedule_for_date.return_value = (22, 0)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = MEETING_DAY
            await _run_scheduled_task("test task", service_fn, bot)

        service_fn.assert_awaited_once_with(
            bot,
            "100",
            "200",
            meeting_hour=22,
            meeting_minute=0,
        )

    async def test_skips_when_no_meeting(self, env_vars, mock_schedule_service):
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = OFF_WEEK
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_not_awaited()

    async def test_skips_when_env_vars_missing(
        self, monkeypatch, mock_schedule_service
    ):
        monkeypatch.delenv("ATTENDANCE_CHANNEL_ID", raising=False)
        monkeypatch.delenv("RETROSPECTIVE_ROLE_ID", raising=False)
        mock_schedule_service.get_effective_schedule_for_date.return_value = (22, 0)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = MEETING_DAY
            await _run_scheduled_task("test task", service_fn, bot)
        service_fn.assert_not_awaited()
