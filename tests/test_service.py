"""Tests for service.py."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from hillkeeper.config import KST
from hillkeeper.attendance import repository
from hillkeeper.attendance.service import send_morning_check, send_evening_reminder


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)


class TestSendMorningCheck:

    async def test_sends_message_with_content_and_embed(self, mock_bot, env_vars, fake_redis):
        await send_morning_check(mock_bot, "100", "200")
        mock_bot._mock_channel.send.assert_called_once()
        call_kwargs = mock_bot._mock_channel.send.call_args[1]
        assert "content" in call_kwargs
        assert "embed" in call_kwargs

    async def test_adds_two_reactions(self, mock_bot, env_vars, fake_redis):
        await send_morning_check(mock_bot, "100", "200")
        assert mock_bot._mock_message.add_reaction.call_count == 2

    async def test_saves_event_to_redis(self, mock_bot, env_vars, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            await send_morning_check(mock_bot, "100", "200")
        fake_redis.hset.assert_called_once()

    async def test_test_mode_uses_short_ttl(self, mock_bot, env_vars, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            await send_morning_check(mock_bot, "100", "200", is_test=True)
        ttl = fake_redis.expire.call_args[0][1]
        assert ttl == 60

    async def test_channel_not_found_returns_early(self, mock_bot, env_vars, fake_redis):
        mock_bot.get_channel.return_value = None
        await send_morning_check(mock_bot, "999", "200")
        fake_redis.hset.assert_not_called()


class TestSendEveningReminder:

    @pytest.fixture
    def setup_evening(self, mock_bot, env_vars, fake_redis):
        """Common setup for evening reminder tests."""
        async def scan_iter(match=None):
            yield f"attendance:event:{FIXED_THURSDAY.date()}:12345"

        fake_redis.scan_iter = scan_iter

        mock_message = AsyncMock()
        mock_message.id = 12345

        role = MagicMock(spec=discord.Role)
        role.id = 200

        member1 = MagicMock(spec=discord.Member)
        member1.id = 1001
        member1.mention = "<@1001>"
        member1.bot = False
        member1.roles = [role]

        member2 = MagicMock(spec=discord.Member)
        member2.id = 1002
        member2.mention = "<@1002>"
        member2.bot = False
        member2.roles = [role]

        bot_user = MagicMock(spec=discord.Member)
        bot_user.id = 999
        bot_user.bot = True

        check_reaction = MagicMock()
        check_reaction.emoji = "✅"

        async def users():
            yield member1
            yield member2
            yield bot_user

        check_reaction.users = users
        mock_message.reactions = [check_reaction]

        channel = mock_bot._mock_channel
        channel.fetch_message = AsyncMock(return_value=mock_message)

        guild = MagicMock()
        guild.get_role = MagicMock(return_value=role)
        guild.get_member = MagicMock(side_effect=lambda uid: {
            1001: member1, 1002: member2
        }.get(uid))
        channel.guild = guild
        mock_message.guild = guild

        return {
            "bot": mock_bot,
            "members": [member1, member2],
            "role": role,
            "channel": channel,
        }

    async def test_sends_reminder_to_participants(self, setup_evening):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            await send_evening_reminder(setup_evening["bot"], "100", "200")
        channel = setup_evening["channel"]
        assert channel.send.call_count == 1
        call_kwargs = channel.send.call_args[1]
        assert "<@1001>" in call_kwargs.get("content", "")

    async def test_sends_no_participants_message(self, mock_bot, env_vars, fake_redis):
        async def scan_iter(match=None):
            yield f"attendance:event:{FIXED_THURSDAY.date()}:12345"

        fake_redis.scan_iter = scan_iter

        mock_message = AsyncMock()
        mock_message.id = 12345
        mock_message.reactions = []

        mock_bot._mock_channel.fetch_message = AsyncMock(return_value=mock_message)

        role = MagicMock(spec=discord.Role)
        role.id = 200
        mock_bot._mock_channel.guild.get_role.return_value = role

        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            await send_evening_reminder(mock_bot, "100", "200")

        call_kwargs = mock_bot._mock_channel.send.call_args[1]
        assert "content" not in call_kwargs or call_kwargs.get("content") is None
        embed = call_kwargs["embed"]
        assert "언덕지기" in embed.title

    async def test_raises_when_no_messages_today(self, mock_bot, env_vars, fake_redis):
        with patch("hillkeeper.attendance.repository.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_THURSDAY
            mock_dt.date = datetime.date
            with pytest.raises(ValueError, match="No attendance messages"):
                await send_evening_reminder(mock_bot, "100", "200")

    async def test_channel_not_found_returns_early(self, mock_bot, env_vars, fake_redis):
        mock_bot.get_channel.return_value = None
        await send_evening_reminder(mock_bot, "999", "200")
