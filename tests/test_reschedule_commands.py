"""Tests for reschedule and schedule commands."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from hillkeeper.config import KST
from hillkeeper.bot.commands import RescheduleGroup


FIXED_THURSDAY = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.id = 123456789
    interaction.user.display_name = "TestUser"

    mock_role = MagicMock(spec=discord.Role)
    mock_role.id = 200
    interaction.user.get_role = MagicMock(return_value=mock_role)
    interaction.user.roles = [mock_role]

    interaction.channel = AsyncMock()
    interaction.guild_id = 999

    return interaction


class TestRescheduleGroupPermission:

    async def test_interaction_check_passes_with_role(self, mock_interaction, env_vars):
        group = RescheduleGroup()
        mock_interaction.user.get_role.return_value = MagicMock()
        result = await group.interaction_check(mock_interaction)
        assert result is True

    async def test_interaction_check_fails_without_role(self, mock_interaction, env_vars):
        group = RescheduleGroup()
        mock_interaction.user.get_role.return_value = None
        result = await group.interaction_check(mock_interaction)
        assert result is False


class TestRescheduleOnceCommand:

    async def test_calls_service_reschedule_once(self, mock_interaction, env_vars):
        with patch("hillkeeper.bot.commands.schedule_service") as mock_service, \
             patch("hillkeeper.bot.commands.schedule_repository") as mock_repo:
            mock_service.reschedule_once = AsyncMock(return_value="변경 메시지")
            mock_repo.get_effective_schedule_for_date = AsyncMock(return_value=(22, 0))

            group = RescheduleGroup()
            day = discord.app_commands.Choice(name="금요일", value=4)
            await group.once.callback(group, mock_interaction, day=day, time="22:00")

            mock_service.reschedule_once.assert_called_once()

    async def test_rejects_invalid_time_format(self, mock_interaction, env_vars):
        with patch("hillkeeper.bot.commands.schedule_service"), \
             patch("hillkeeper.bot.commands.schedule_repository"):
            group = RescheduleGroup()
            day = discord.app_commands.Choice(name="금요일", value=4)
            await group.once.callback(group, mock_interaction, day=day, time="invalid")
            # Should send error followup
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args
            assert "형식" in call_args[0][0] or "형식" in str(call_args)


class TestRescheduleSkipCommand:

    async def test_calls_service_skip(self, mock_interaction, env_vars):
        with patch("hillkeeper.bot.commands.schedule_service") as mock_service, \
             patch("hillkeeper.bot.commands.schedule_repository"):
            mock_service.skip_this_week = AsyncMock(return_value="취소 메시지")

            group = RescheduleGroup()
            await group.skip.callback(group, mock_interaction)

            mock_service.skip_this_week.assert_called_once()
