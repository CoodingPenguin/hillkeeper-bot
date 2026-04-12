"""Tests for schedule/repository.py."""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST, DEFAULT_MEETING_WEEKDAY, DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE
from hillkeeper.schedule import repository
from hillkeeper.schedule.repository import (
    _default_key, _override_key,
    DefaultSchedule, ScheduleOverride,
)


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
FIXED_DATE = FIXED_THURSDAY.date()
FIXED_MONDAY = datetime.datetime(2026, 4, 6, 9, 0, 0, tzinfo=KST)


@pytest.fixture(autouse=True)
def patch_datetime():
    """Patch datetime.now to a fixed Thursday."""
    with patch("hillkeeper.schedule.repository.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_THURSDAY
        mock_dt.date = datetime.date
        yield mock_dt


# --- Key helpers ---

class TestKeyHelpers:

    def test_default_key(self):
        assert _default_key() == "schedule:default"

    def test_override_key(self):
        assert _override_key("2026-04-17") == "schedule:override:2026-04-17"


# --- save_default / get_default ---

class TestSaveDefault:

    async def test_calls_hset_with_correct_key(self, fake_redis):
        await repository.save_default(weekday=3, hour=22, minute=0, updated_by=123456789)
        key = fake_redis.hset.call_args[0][0]
        assert key == "schedule:default"

    async def test_stores_all_fields(self, fake_redis):
        await repository.save_default(weekday=3, hour=22, minute=0, updated_by=123456789)
        mapping = fake_redis.hset.call_args[1]["mapping"]
        assert mapping["weekday"] == "3"
        assert mapping["hour"] == "22"
        assert mapping["minute"] == "0"
        assert mapping["updated_by"] == "123456789"
        assert "updated_at" in mapping

    async def test_no_ttl_set(self, fake_redis):
        await repository.save_default(weekday=3, hour=22, minute=0, updated_by=123456789)
        fake_redis.expire.assert_not_called()


class TestGetDefault:

    async def test_returns_default_schedule(self, fake_redis):
        fake_redis.hgetall.return_value = {
            "weekday": "3",
            "hour": "22",
            "minute": "0",
            "updated_by": "123456789",
            "updated_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_default()
        assert isinstance(result, DefaultSchedule)
        assert result.weekday == 3
        assert result.hour == 22
        assert result.minute == 0
        assert result.updated_by == 123456789

    async def test_returns_none_when_missing(self, fake_redis):
        fake_redis.hgetall.return_value = {}
        result = await repository.get_default()
        assert result is None


# --- save_override / get_override / delete_override ---

class TestSaveOverride:

    async def test_calls_hset_with_correct_key(self, fake_redis):
        await repository.save_override(
            date="2026-04-17", hour=22, minute=0, is_skip=False, created_by=123456789
        )
        key = fake_redis.hset.call_args[0][0]
        assert key == "schedule:override:2026-04-17"

    async def test_stores_all_fields_for_reschedule(self, fake_redis):
        await repository.save_override(
            date="2026-04-17", hour=22, minute=0, is_skip=False, created_by=123456789
        )
        mapping = fake_redis.hset.call_args[1]["mapping"]
        assert mapping["date"] == "2026-04-17"
        assert mapping["hour"] == "22"
        assert mapping["minute"] == "0"
        assert mapping["is_skip"] == "false"
        assert mapping["created_by"] == "123456789"

    async def test_stores_skip_fields(self, fake_redis):
        await repository.save_override(
            date="2026-04-17", hour=None, minute=None, is_skip=True, created_by=123456789
        )
        mapping = fake_redis.hset.call_args[1]["mapping"]
        assert mapping["is_skip"] == "true"
        assert mapping["hour"] == ""
        assert mapping["minute"] == ""

    async def test_sets_default_ttl(self, fake_redis):
        await repository.save_override(
            date="2026-04-17", hour=22, minute=0, is_skip=False, created_by=123456789
        )
        fake_redis.expire.assert_called_once()
        ttl = fake_redis.expire.call_args[0][1]
        assert ttl == repository.TTL_7_DAYS


class TestGetOverride:

    async def test_returns_schedule_override(self, fake_redis):
        fake_redis.hgetall.return_value = {
            "date": "2026-04-17",
            "hour": "22",
            "minute": "0",
            "is_skip": "false",
            "created_by": "123456789",
            "created_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_override("2026-04-17")
        assert isinstance(result, ScheduleOverride)
        assert result.hour == 22
        assert result.minute == 0
        assert result.is_skip is False

    async def test_returns_skip_override(self, fake_redis):
        fake_redis.hgetall.return_value = {
            "date": "2026-04-17",
            "hour": "",
            "minute": "",
            "is_skip": "true",
            "created_by": "123456789",
            "created_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_override("2026-04-17")
        assert result.is_skip is True
        assert result.hour is None
        assert result.minute is None

    async def test_returns_none_when_missing(self, fake_redis):
        fake_redis.hgetall.return_value = {}
        result = await repository.get_override("2026-04-17")
        assert result is None


class TestDeleteOverride:

    async def test_calls_delete_with_correct_key(self, fake_redis):
        await repository.delete_override("2026-04-17")
        key = fake_redis.delete.call_args[0][0]
        assert key == "schedule:override:2026-04-17"


# --- get_effective_schedule_for_date ---

class TestGetEffectiveScheduleForDate:

    async def test_returns_override_time_when_override_exists(self, fake_redis):
        """Override takes priority over default."""
        fake_redis.hgetall.return_value = {
            "date": "2026-04-09",
            "hour": "21",
            "minute": "30",
            "is_skip": "false",
            "created_by": "123456789",
            "created_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_effective_schedule_for_date(FIXED_DATE)
        assert result == (21, 30)

    async def test_returns_none_when_skip_override(self, fake_redis):
        """Skip override means no meeting."""
        fake_redis.hgetall.return_value = {
            "date": "2026-04-09",
            "hour": "",
            "minute": "",
            "is_skip": "true",
            "created_by": "123456789",
            "created_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_effective_schedule_for_date(FIXED_DATE)
        assert result is None

    async def test_returns_default_on_matching_weekday(self, fake_redis):
        """No override, today matches default weekday → return default time."""
        # First call: get_override returns empty (no override)
        # Second call: get_default returns default schedule
        fake_redis.hgetall.side_effect = [
            {},  # get_override → not found
            {    # get_default → Thursday 22:00
                "weekday": "3",
                "hour": "22",
                "minute": "0",
                "updated_by": "123456789",
                "updated_at": "2026-04-09T09:00:00+09:00",
            },
        ]
        # FIXED_DATE is Thursday (weekday=3), matches default weekday=3
        result = await repository.get_effective_schedule_for_date(FIXED_DATE)
        assert result == (22, 0)

    async def test_returns_none_on_non_matching_weekday(self, fake_redis):
        """No override, today doesn't match default weekday → no meeting."""
        fake_redis.hgetall.side_effect = [
            {},  # get_override → not found
            {    # get_default → Thursday
                "weekday": "3",
                "hour": "22",
                "minute": "0",
                "updated_by": "123456789",
                "updated_at": "2026-04-09T09:00:00+09:00",
            },
        ]
        # Monday (weekday=0) doesn't match default weekday=3
        monday = FIXED_MONDAY.date()
        result = await repository.get_effective_schedule_for_date(monday)
        assert result is None

    async def test_falls_back_to_hardcoded_on_thursday(self, fake_redis):
        """No override, no default in Redis → hardcoded Thursday 22:00 fallback."""
        fake_redis.hgetall.side_effect = [
            {},  # get_override → not found
            {},  # get_default → not found
        ]
        # FIXED_DATE is Thursday → matches hardcoded THURSDAY
        result = await repository.get_effective_schedule_for_date(FIXED_DATE)
        assert result == (DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE)

    async def test_falls_back_to_none_on_non_thursday(self, fake_redis):
        """No override, no default, not Thursday → no meeting."""
        fake_redis.hgetall.side_effect = [
            {},  # get_override → not found
            {},  # get_default → not found
        ]
        monday = FIXED_MONDAY.date()
        result = await repository.get_effective_schedule_for_date(monday)
        assert result is None
