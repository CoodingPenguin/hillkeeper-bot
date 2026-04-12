"""repository.py 테스트"""
import datetime
from unittest.mock import AsyncMock, patch

import pytest

from hillkeeper.config import KST
from hillkeeper.attendance import repository
from hillkeeper.attendance.repository import (
    _event_key, _response_key, _parse_id_from_key,
    AttendanceEvent, UserResponse,
)


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
FIXED_DATE = FIXED_THURSDAY.date()


@pytest.fixture(autouse=True)
def patch_datetime():
    """datetime.now를 고정된 목요일로 패치."""
    with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_THURSDAY
        mock_dt.date = datetime.date
        yield mock_dt


class TestSaveEvent:

    async def test_calls_hset_with_correct_key(self, fake_redis):
        await repository.save_event(12345, channel_id=100, role_id=200)
        key = fake_redis.hset.call_args[0][0]
        assert key == f"attendance:event:{FIXED_DATE}:12345"

    async def test_stores_all_fields(self, fake_redis):
        await repository.save_event(12345, channel_id=100, role_id=200)
        mapping = fake_redis.hset.call_args[1]["mapping"]
        assert mapping["message_id"] == "12345"
        assert mapping["channel_id"] == "100"
        assert mapping["role_id"] == "200"
        assert "created_at" in mapping

    async def test_sets_default_ttl(self, fake_redis):
        await repository.save_event(12345, channel_id=100, role_id=200)
        fake_redis.expire.assert_called_once()
        ttl = fake_redis.expire.call_args[0][1]
        assert ttl == repository.TTL_7_DAYS

    async def test_sets_custom_ttl(self, fake_redis):
        await repository.save_event(12345, channel_id=100, role_id=200, ttl=60)
        ttl = fake_redis.expire.call_args[0][1]
        assert ttl == 60


class TestSaveResponse:

    async def test_calls_hset_with_correct_key(self, fake_redis):
        await repository.save_response(12345, 1001, username="User", response="yes")
        key = fake_redis.hset.call_args[0][0]
        assert key == "attendance:response:12345:1001"

    async def test_stores_response_field(self, fake_redis):
        await repository.save_response(12345, 1001, username="User", response="no")
        mapping = fake_redis.hset.call_args[1]["mapping"]
        assert mapping["response"] == "no"
        assert mapping["username"] == "User"


class TestGetTodayMessages:

    async def test_returns_parsed_ids(self, fake_redis):
        async def scan_iter(match=None):
            yield f"attendance:event:{FIXED_DATE}:111"
            yield f"attendance:event:{FIXED_DATE}:222"

        fake_redis.scan_iter = scan_iter
        result = await repository.get_today_messages()
        assert sorted(result) == [111, 222]

    async def test_returns_empty_list(self, fake_redis):
        result = await repository.get_today_messages()
        assert result == []


class TestGetEvent:

    async def test_returns_attendance_event(self, fake_redis):
        fake_redis.hgetall.return_value = {
            "message_id": "12345",
            "channel_id": "100",
            "role_id": "200",
            "created_at": "2026-04-09T09:00:00+09:00",
        }
        result = await repository.get_event(12345)
        assert isinstance(result, AttendanceEvent)
        assert result.message_id == 12345
        assert result.channel_id == 100
        assert result.role_id == 200

    async def test_returns_none_when_missing(self, fake_redis):
        fake_redis.hgetall.return_value = {}
        result = await repository.get_event(99999)
        assert result is None


class TestGetResponses:

    async def test_returns_user_response_objects(self, fake_redis):
        async def scan_iter(match=None):
            yield "attendance:response:12345:1001"
            yield "attendance:response:12345:1002"

        fake_redis.scan_iter = scan_iter
        fake_redis.hgetall.side_effect = [
            {"user_id": "1001", "username": "User1", "response": "yes", "timestamp": "2026-04-09T09:00:00+09:00"},
            {"user_id": "1002", "username": "User2", "response": "no", "timestamp": "2026-04-09T09:01:00+09:00"},
        ]
        result = await repository.get_responses(12345)
        assert len(result) == 2
        assert isinstance(result[0], UserResponse)
        assert result[0].response == "yes"


class TestKeyHelpers:

    def test_event_key(self):
        key = _event_key(FIXED_DATE, 12345)
        assert key == f"attendance:event:{FIXED_DATE}:12345"

    def test_response_key(self):
        key = _response_key(12345, 1001)
        assert key == "attendance:response:12345:1001"

    def test_parse_id_from_key(self):
        assert _parse_id_from_key(f"attendance:event:{FIXED_DATE}:12345") == 12345
        assert _parse_id_from_key("attendance:response:12345:1001") == 1001


class TestDeleteEvent:

    async def test_calls_delete_with_correct_key(self, fake_redis):
        await repository.delete_event(12345)
        key = fake_redis.delete.call_args[0][0]
        assert key == f"attendance:event:{FIXED_DATE}:12345"
