"""메시지 템플릿"""
import discord
from .config import EMOJI_CHECK, EMOJI_CROSS


def create_morning_check_embed(role_id: int, voice_channel_id: int) -> tuple[str, discord.Embed]:
    """
    아침 출석 체크 Embed를 생성합니다.

    Args:
        role_id: 멘션할 역할 ID
        voice_channel_id: 음성 채널 ID

    Returns:
        (content, embed) 튜플
    """
    content = f"<@&{role_id}>"

    embed = discord.Embed(
        title="📋️회고 모임 참석 여부 확인",
        description=(
            "오늘 밤 10시 회고 모임이 있어요!\n"
            "참여 여부를 체크해주세요.\n"
            f"- {EMOJI_CHECK} `참석합니다`\n"
            f"- {EMOJI_CROSS} `불참합니다`"
        ),
        color=0x58ABFF,  # 파란색
    )

    embed.add_field(name="시간", value="오늘 오후 10시", inline=True)
    embed.add_field(name="채널", value=f"<#{voice_channel_id}>", inline=True)

    embed.set_footer(text="⚠️ 참석과 불참을 모두 누르면 마지막 선택만 남아요.")

    return content, embed


def create_evening_reminder_embed(mentions: str, voice_channel_id: int) -> tuple[str, discord.Embed]:
    """
    저녁 리마인더 Embed를 생성합니다.

    Args:
        mentions: 멘션할 사용자 문자열
        voice_channel_id: 음성 채널 ID

    Returns:
        (content, embed) 튜플
    """
    content = mentions

    embed = discord.Embed(
        title="🔔 회고 모임 시작 알림",
        description=f"곧 회고 모임이 시작돼요!\n15분 후(오후 10시) <#{voice_channel_id}>로 들어와 주세요.",
        color=0xF1C40F  # 주황색
    )

    return content, embed


def create_no_participants_embed() -> discord.Embed:
    """
    참여자 없음 Embed를 생성합니다.

    Returns:
        embed 객체
    """
    embed = discord.Embed(
        title="🐮 언덕지기가 혼자 언덕을 지키고 있어요!",
        description="오늘은 언덕을 잘 지켜둘게요.\n다음 주에 만나요!",
        color=0x34A5DB  # 진한 파란색
    )

    return embed
