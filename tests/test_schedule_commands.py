"""Tests for schedule-related slash commands."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from hillkeeper.bot.commands import register_commands


@pytest.fixture
def registered_commands():
    """Register commands on a lightweight bot and return callbacks by name."""
    callbacks = {}
    bot = MagicMock()
    bot.tree.sync = AsyncMock(return_value=[])

    def command(*, name, description):
        def decorator(callback):
            callbacks[name] = callback
            return callback
        return decorator

    bot.tree.command = command
    register_commands(bot)
    return callbacks


@pytest.fixture
def interaction():
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.channel = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.id = 123
    interaction.user.display_name = "TestUser"
    interaction.user.get_role.return_value = MagicMock()
    return interaction


async def test_schedule_shows_next_meeting(
    registered_commands, interaction, env_vars
):
    meeting = {
        "date": datetime.date(2026, 7, 7),
        "weekday": 1,
        "day_name": "화요일",
        "hour": 22,
        "minute": 0,
    }
    with patch(
        "hillkeeper.bot.commands.schedule_service.get_next_meeting",
        AsyncMock(return_value=meeting),
    ):
        await registered_commands["schedule"](interaction)

    embed = interaction.followup.send.call_args.kwargs["embed"]
    assert "2026년 7월 7일 화요일 22:00" in embed.description


async def test_skip_cancels_next_meeting(
    registered_commands, interaction, env_vars
):
    meeting = {
        "date": datetime.date(2026, 7, 7),
        "weekday": 1,
        "day_name": "화요일",
        "hour": 22,
        "minute": 0,
    }
    with patch(
        "hillkeeper.bot.commands.schedule_service.skip_next_meeting",
        AsyncMock(return_value=meeting),
    ) as skip_next:
        await registered_commands["skip"](interaction)

    skip_next.assert_awaited_once_with(user_id=123)
    interaction.channel.send.assert_awaited_once()


async def test_skip_requires_retrospective_role(
    registered_commands, interaction, env_vars
):
    interaction.user.get_role.return_value = None
    await registered_commands["skip"](interaction)
    interaction.response.send_message.assert_awaited_once()


def test_reschedule_command_is_not_registered(registered_commands):
    assert "reschedule" not in registered_commands
