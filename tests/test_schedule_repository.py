"""Tests for schedule/repository.py."""
from hillkeeper.schedule import repository
from hillkeeper.schedule.repository import ScheduleOverride, _override_key


def test_override_key():
    assert _override_key("2026-07-07") == "schedule:override:2026-07-07"


async def test_save_skip_override(fake_redis):
    await repository.save_override(
        date="2026-07-07",
        hour=None,
        minute=None,
        is_skip=True,
        created_by=123,
    )

    mapping = fake_redis.hset.call_args.kwargs["mapping"]
    assert mapping["is_skip"] == "true"
    assert mapping["hour"] == ""
    assert mapping["minute"] == ""
    fake_redis.expire.assert_awaited_once_with(
        "schedule:override:2026-07-07",
        repository.TTL_30_DAYS,
    )


async def test_get_skip_override(fake_redis):
    fake_redis.hgetall.return_value = {
        "date": "2026-07-07",
        "hour": "",
        "minute": "",
        "is_skip": "true",
        "created_by": "123",
        "created_at": "2026-06-22T09:00:00+09:00",
    }

    result = await repository.get_override("2026-07-07")

    assert isinstance(result, ScheduleOverride)
    assert result.is_skip is True
    assert result.hour is None
    assert result.minute is None


async def test_get_override_returns_none_when_missing(fake_redis):
    assert await repository.get_override("2026-07-07") is None


async def test_delete_override(fake_redis):
    await repository.delete_override("2026-07-07")
    fake_redis.delete.assert_awaited_once_with("schedule:override:2026-07-07")
