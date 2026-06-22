"""Discord message templates."""
import datetime

import discord
from .config import (
    EMOJI_CHECK, EMOJI_CROSS,
    COLOR_BLUE, COLOR_YELLOW, COLOR_DARK_BLUE, COLOR_GREEN,
    DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE,
)


def _format_time(hour: int, minute: int) -> str:
    """Format hour and minute as HH:MM string."""
    return f"{hour:02d}:{minute:02d}"


def create_morning_check_embed(
    role_id: int, voice_channel_id: int, *,
    meeting_hour: int = DEFAULT_MEETING_HOUR,
    meeting_minute: int = DEFAULT_MEETING_MINUTE,
) -> tuple[str, discord.Embed]:
    """
    Build the morning attendance check embed.

    Args:
        role_id: Role ID to mention.
        voice_channel_id: Voice channel ID to link.
        meeting_hour: Meeting hour for display.
        meeting_minute: Meeting minute for display.

    Returns:
        A (content, embed) tuple.
    """
    content = f"<@&{role_id}>"
    time_str = _format_time(meeting_hour, meeting_minute)

    embed = discord.Embed(
        title="📋️회고 모임 참석 여부 확인",
        description=(
            f"오늘 {time_str}에 회고 모임이 있어요!\n"
            "참석 여부를 체크해주세요.\n"
            f"- {EMOJI_CHECK} `참석합니다`\n"
            f"- {EMOJI_CROSS} `불참합니다`"
        ),
        color=COLOR_BLUE,
    )

    embed.add_field(name="시간", value=f"오늘 {time_str}", inline=True)
    embed.add_field(name="채널", value=f"<#{voice_channel_id}>", inline=True)

    embed.set_footer(text="⚠️ 참석과 불참을 모두 누르면 마지막 선택만 남아요.")

    return content, embed


def create_evening_reminder_embed(
    mentions: str, voice_channel_id: int, *,
    meeting_hour: int = DEFAULT_MEETING_HOUR,
    meeting_minute: int = DEFAULT_MEETING_MINUTE,
) -> tuple[str, discord.Embed]:
    """
    Build the evening reminder embed.

    Args:
        mentions: Mention string for participating users.
        voice_channel_id: Voice channel ID to link.
        meeting_hour: Meeting hour for display.
        meeting_minute: Meeting minute for display.

    Returns:
        A (content, embed) tuple.
    """
    content = mentions
    time_str = _format_time(meeting_hour, meeting_minute)

    embed = discord.Embed(
        title="🔔 회고 모임 시작 알림",
        description=(
            f"곧 회고 모임이 시작돼요!\n"
            f"{time_str}에 <#{voice_channel_id}>로 들어와 주세요."
        ),
        color=COLOR_YELLOW,
    )

    return content, embed


def create_no_participants_embed() -> discord.Embed:
    """
    Build the "no participants" embed.

    Returns:
        A discord.Embed instance.
    """
    embed = discord.Embed(
        title="🐮 언덕지기가 혼자 언덕을 지키고 있어요!",
        description="오늘은 언덕을 잘 지켜둘게요.\n대신, 언덕지기에게 이번 주 이야기를 조금 들려주세요!",
        color=COLOR_DARK_BLUE,
    )

    return embed


def create_schedule_skipped_embed(
    *, date: datetime.date, day_name: str
) -> discord.Embed:
    """
    Build the schedule skip notification embed.

    Args:
        date: Date of the skipped meeting.
        day_name: Korean day name of the skipped date.

    Returns:
        A discord.Embed instance.
    """
    embed = discord.Embed(
        title="📅 회고 일정 취소",
        description=(
            f"{date.month}월 {date.day}일 {day_name} 회고 모임이 취소되었습니다."
        ),
        color=COLOR_GREEN,
    )
    return embed


def create_schedule_view_embed(
    *, date: datetime.date, day_name: str, hour: int, minute: int,
) -> discord.Embed:
    """
    Build the schedule view embed for /schedule command.

    Args:
        date: Date of the next meeting.
        day_name: Korean day name of the next meeting.
        hour: Meeting hour.
        minute: Meeting minute.

    Returns:
        A discord.Embed instance.
    """
    time_str = _format_time(hour, minute)
    embed = discord.Embed(
        title="📋 다가오는 회고 일정",
        description=(
            f"**{date.year}년 {date.month}월 {date.day}일 "
            f"{day_name} {time_str}**"
        ),
        color=COLOR_BLUE,
    )
    return embed
