"""Shared test fixtures."""
import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from hillkeeper.config import KST


# --- Time fixtures ---

THURSDAY_DATETIME = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)
MONDAY_DATETIME = datetime.datetime(2026, 4, 6, 9, 0, 0, tzinfo=KST)


@pytest.fixture
def thursday_now():
    """Freeze datetime.now to a known Thursday."""
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = THURSDAY_DATETIME
        mock_dt.side_effect = lambda *args, **kwargs: datetime.datetime(*args, **kwargs)
        yield mock_dt


# --- Redis fixture ---

@pytest.fixture
def fake_redis():
    """Replace redis_client._client with an AsyncMock."""
    mock_client = AsyncMock()
    mock_client.hset = AsyncMock()
    mock_client.expire = AsyncMock()
    mock_client.hgetall = AsyncMock(return_value={})
    mock_client.delete = AsyncMock()

    async def empty_scan_iter(match=None):
        return
        yield

    mock_client.scan_iter = empty_scan_iter

    with patch("hillkeeper.database.redis.redis_client._client", mock_client):
        yield mock_client


# --- Discord fixtures ---

def _make_member(user_id: int, name: str, *, bot: bool = False, roles: list | None = None):
    """Create a mock Discord Member for testing."""
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.display_name = name
    member.mention = f"<@{user_id}>"
    member.bot = bot
    member.roles = roles or []
    return member


@pytest.fixture
def mock_bot():
    """Provide a Discord bot AsyncMock with pre-configured channel/guild."""
    bot = AsyncMock()
    bot.user = MagicMock()
    bot.user.id = 999
    bot.user.bot = True

    mock_channel = AsyncMock()
    mock_channel.id = 100
    mock_channel.guild = MagicMock()

    mock_message = AsyncMock()
    mock_message.id = 12345
    mock_message.add_reaction = AsyncMock()

    mock_channel.send = AsyncMock(return_value=mock_message)
    bot.get_channel = MagicMock(return_value=mock_channel)

    mock_role = MagicMock(spec=discord.Role)
    mock_role.id = 200

    mock_member = _make_member(1001, "TestUser", roles=[mock_role])
    mock_channel.guild.get_role = MagicMock(return_value=mock_role)
    mock_channel.guild.get_member = MagicMock(return_value=mock_member)
    bot.get_guild = MagicMock(return_value=mock_channel.guild)

    bot._mock_channel = mock_channel
    bot._mock_message = mock_message
    bot._mock_role = mock_role
    bot._mock_member = mock_member

    return bot


@pytest.fixture
def env_vars(monkeypatch):
    """Set required environment variables for testing."""
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("ATTENDANCE_CHANNEL_ID", "100")
    monkeypatch.setenv("RETROSPECTIVE_ROLE_ID", "200")
    monkeypatch.setenv("VOICE_CHANNEL_ID", "300")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("TEST_CHANNEL_ID", "400")
    monkeypatch.setenv("TEST_ROLE_ID", "500")
