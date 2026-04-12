"""Tests for events.py."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from hillkeeper.config import KST
from hillkeeper.bot.events import register_events, handle_attendance_reaction


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)


def _make_payload(*, user_id=1001, emoji="✅", message_id=12345, guild_id=1, channel_id=100):
    payload = MagicMock()
    payload.user_id = user_id
    payload.emoji = MagicMock()
    payload.emoji.__str__ = MagicMock(return_value=emoji)
    payload.message_id = message_id
    payload.guild_id = guild_id
    payload.channel_id = channel_id
    return payload


class TestRegisterEvents:

    def test_register_events_does_not_raise(self):
        bot = MagicMock()
        register_events(bot)


class TestHandleAttendanceReaction:

    async def test_ignores_bot_reactions(self, mock_bot, fake_redis):
        payload = _make_payload(user_id=mock_bot.user.id)
        await handle_attendance_reaction(mock_bot, payload)
        fake_redis.hset.assert_not_called()

    async def test_ignores_non_attendance_emoji(self, mock_bot, fake_redis):
        payload = _make_payload(emoji="🎉")
        await handle_attendance_reaction(mock_bot, payload)
        fake_redis.hset.assert_not_called()

    async def test_ignores_non_event_messages(self, mock_bot, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            fake_redis.hgetall.return_value = {}
            payload = _make_payload()
            await handle_attendance_reaction(mock_bot, payload)
            # hset should not be called for save_response
            fake_redis.hset.assert_not_called()

    async def test_saves_yes_response(self, mock_bot, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            fake_redis.hgetall.return_value = {"message_id": "12345", "channel_id": "100", "role_id": "200", "created_at": "2026-04-09T09:00:00+09:00"}
            payload = _make_payload(emoji="✅")
            await handle_attendance_reaction(mock_bot, payload)
            mapping = fake_redis.hset.call_args[1]["mapping"]
            assert mapping["response"] == "yes"

    async def test_saves_no_response(self, mock_bot, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            fake_redis.hgetall.return_value = {"message_id": "12345", "channel_id": "100", "role_id": "200", "created_at": "2026-04-09T09:00:00+09:00"}
            payload = _make_payload(emoji="❌")
            await handle_attendance_reaction(mock_bot, payload)
            mapping = fake_redis.hset.call_args[1]["mapping"]
            assert mapping["response"] == "no"

    async def test_removes_opposite_emoji(self, mock_bot, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            fake_redis.hgetall.return_value = {"message_id": "12345", "channel_id": "100", "role_id": "200", "created_at": "2026-04-09T09:00:00+09:00"}

            mock_message = AsyncMock()
            mock_bot.get_channel.return_value.fetch_message = AsyncMock(return_value=mock_message)

            payload = _make_payload(emoji="✅")
            await handle_attendance_reaction(mock_bot, payload)
            mock_message.remove_reaction.assert_called_once()
            removed_emoji = mock_message.remove_reaction.call_args[0][0]
            assert removed_emoji == "❌"
