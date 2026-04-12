"""Discord message templates."""
import discord
from .config import EMOJI_CHECK, EMOJI_CROSS, COLOR_BLUE, COLOR_YELLOW, COLOR_DARK_BLUE


def create_morning_check_embed(role_id: int, voice_channel_id: int) -> tuple[str, discord.Embed]:
    """
    Build the morning attendance check embed.

    Args:
        role_id: Role ID to mention.
        voice_channel_id: Voice channel ID to link.

    Returns:
        A (content, embed) tuple.
    """
    content = f"<@&{role_id}>"

    embed = discord.Embed(
        title="📋️회고 모임 참석 여부 확인",
        description=(
            "오늘 밤 10시 회고 모임이 있어요!\n"
            "참석 여부를 체크해주세요.\n"
            f"- {EMOJI_CHECK} `참석합니다`\n"
            f"- {EMOJI_CROSS} `불참합니다`"
        ),
        color=COLOR_BLUE,
    )

    embed.add_field(name="시간", value="오늘 오후 10시", inline=True)
    embed.add_field(name="채널", value=f"<#{voice_channel_id}>", inline=True)

    embed.set_footer(text="⚠️ 참석과 불참을 모두 누르면 마지막 선택만 남아요.")

    return content, embed


def create_evening_reminder_embed(mentions: str, voice_channel_id: int) -> tuple[str, discord.Embed]:
    """
    Build the evening reminder embed.

    Args:
        mentions: Mention string for participating users.
        voice_channel_id: Voice channel ID to link.

    Returns:
        A (content, embed) tuple.
    """
    content = mentions

    embed = discord.Embed(
        title="🔔 회고 모임 시작 알림",
        description=f"곧 회고 모임이 시작돼요!\n15분 후(오후 10시) <#{voice_channel_id}>로 들어와 주세요.",
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
        description="오늘은 언덕을 잘 지켜둘게요.\n다음 주에 만나요!\n\n📖 대신, 언덕지기에게 이번 주 이야기를 들려주세요!",
        color=COLOR_DARK_BLUE,
    )

    return embed
