"""tasks.py 테스트"""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST
from hillkeeper.bot.tasks import _is_thursday, _run_thursday_task


THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
MONDAY = datetime.datetime(2026, 4, 6, 9, 0, 0, tzinfo=KST)


class TestIsThursday:

    def test_returns_true_on_thursday(self):
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            assert _is_thursday() is True

    def test_returns_false_on_monday(self):
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = MONDAY
            assert _is_thursday() is False

    def test_returns_false_on_friday(self):
        friday = datetime.datetime(2026, 4, 10, 9, 0, 0, tzinfo=KST)
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = friday
            assert _is_thursday() is False

    def test_returns_false_on_sunday(self):
        sunday = datetime.datetime(2026, 4, 12, 9, 0, 0, tzinfo=KST)
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = sunday
            assert _is_thursday() is False


class TestRunThursdayTask:

    async def test_calls_service_on_thursday(self, env_vars):
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_thursday_task("test task", service_fn, bot)
        service_fn.assert_called_once()

    async def test_skips_on_non_thursday(self, env_vars):
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = MONDAY
            await _run_thursday_task("test task", service_fn, bot)
        service_fn.assert_not_called()

    async def test_skips_when_env_vars_missing(self, monkeypatch):
        monkeypatch.delenv("ATTENDANCE_CHANNEL_ID", raising=False)
        monkeypatch.delenv("RETROSPECTIVE_ROLE_ID", raising=False)
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_thursday_task("test task", service_fn, bot)
        service_fn.assert_not_called()

    async def test_passes_channel_and_role_to_service(self, env_vars):
        service_fn = AsyncMock()
        bot = AsyncMock()
        with patch("hillkeeper.bot.tasks.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = THURSDAY
            await _run_thursday_task("test task", service_fn, bot)
        service_fn.assert_called_once_with(bot, "100", "200")
