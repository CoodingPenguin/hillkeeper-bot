"""테스트 공통 fixture"""
import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import discord
import pytest

from hillkeeper.config import KST


# --- 시간 fixture ---

THURSDAY_DATETIME = datetime.datetime(2026, 4, 9, 9, 0, 0, tzinfo=KST)  # 목요일
MONDAY_DATETIME = datetime.datetime(2026, 4, 6, 9, 0, 0, tzinfo=KST)  # 월요일


@pytest.fixture
def thursday_now():
    """
    datetime.datetime.now를 목요일로 고정하는 fixture.
    """
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = THURSDAY_DATETIME
        mock_dt.side_effect = lambda *args, **kwargs: datetime.datetime(*args, **kwargs)
        yield mock_dt


# --- Redis fixture ---

@pytest.fixture
def fake_redis():
    """
    redis_client._client를 AsyncMock으로 교체하는 fixture.
    """
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


# --- Discord fixture ---

def _make_member(user_id: int, name: str, *, bot: bool = False, roles: list | None = None):
    """테스트용 Discord Member mock을 생성하는 헬퍼."""
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.display_name = name
    member.mention = f"<@{user_id}>"
    member.bot = bot
    member.roles = roles or []
    return member


@pytest.fixture
def mock_bot():
    """Discord 봇 AsyncMock fixture."""
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
    """필수 환경변수를 설정하는 fixture."""
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("ATTENDANCE_CHANNEL_ID", "100")
    monkeypatch.setenv("RETROSPECTIVE_ROLE_ID", "200")
    monkeypatch.setenv("VOICE_CHANNEL_ID", "300")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("TEST_CHANNEL_ID", "400")
    monkeypatch.setenv("TEST_ROLE_ID", "500")
