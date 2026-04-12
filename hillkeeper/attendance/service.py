import logging

import discord

from ..config import EMOJI_CHECK, EMOJI_CROSS, get_env
from ..messages import create_morning_check_embed, create_evening_reminder_embed, create_no_participants_embed
from ..utils import get_users_who_reacted
from . import repository

logger = logging.getLogger('hillkeeper')


def _get_channel(bot, channel_id: str) -> discord.TextChannel | None:
    """
    채널 객체를 가져옵니다. 없으면 로그를 남기고 None을 반환합니다.

    Args:
        bot: Discord 봇 인스턴스
        channel_id: 채널 ID 문자열
    """
    channel = bot.get_channel(int(channel_id))
    if not channel:
        logger.error(f"Channel not found: {channel_id}")
    return channel


async def _get_participated_members(
    channel, message_id: int, role: discord.Role
) -> set[discord.Member]:
    """
    출석 체크 메시지에서 참여한 멤버를 수집합니다.

    Args:
        channel: Discord 채널
        message_id: 출석 체크 메시지 ID
        role: 필터링할 역할

    Returns:
        참여한 멤버 집합

    Raises:
        ValueError: 메시지를 가져오지 못한 경우
    """
    try:
        message = await channel.fetch_message(message_id)
        return await get_users_who_reacted(
            message,
            EMOJI_CHECK,
            exclude_bots=True,
            filter_role=role
        )
    except Exception as e:
        logger.error(f"Failed to fetch message {message_id}: {e}")
        await repository.delete_event(message_id)
        raise ValueError(f"Failed to fetch attendance message: {message_id}") from e


async def _send_reminder_or_empty(channel, members: set, voice_channel_id: str):
    """
    참여자 수에 따라 리마인더 또는 안내 메시지를 전송합니다.

    Args:
        channel: Discord 채널
        members: 참여한 멤버 집합
        voice_channel_id: 음성 채널 ID 문자열
    """
    if members and len(members) > 1:
        mentions = " ".join([member.mention for member in members])
        content, embed = create_evening_reminder_embed(mentions, int(voice_channel_id))
        await channel.send(content=content, embed=embed)
        logger.info(f"Evening reminder sent to {len(members)} members")
    else:
        embed = create_no_participants_embed()
        await channel.send(embed=embed)
        logger.info(f"Not enough participants: {len(members) if members else 0} members")


async def send_morning_check(bot, channel_id: str, role_id: str, *, is_test: bool = False):
    """
    아침 출석 체크 메시지를 전송합니다.
    지정된 채널에 출석 체크 메시지를 보내고 ✅/❌ 이모지를 추가합니다.
    테스트 모드에서는 1분 TTL, 프로덕션에서는 7일 TTL로 Redis에 저장됩니다.

    Args:
        bot: Discord 봇 인스턴스
        channel_id: 메시지를 전송할 채널 ID
        role_id: 멘션할 역할 ID
        is_test: 테스트 모드 여부 (기본값: False)
    """
    try:
        channel = _get_channel(bot, channel_id)
        if not channel:
            return

        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)
        content, embed = create_morning_check_embed(int(role_id), int(voice_channel_id))
        message = await channel.send(content=content, embed=embed)

        await message.add_reaction(EMOJI_CHECK)
        await message.add_reaction(EMOJI_CROSS)

        ttl = 60 if is_test else repository.TTL_7_DAYS
        await repository.save_event(
            message.id,
            channel_id=channel.id,
            role_id=int(role_id),
            ttl=ttl
        )

        logger.info(f"Morning check message sent: {message.id} (test={is_test}, ttl={ttl}s)")

    except Exception as e:
        logger.error(f"Failed to send morning check message: {e}")
        raise


async def send_evening_reminder(bot, channel_id: str, role_id: str):
    """
    저녁 리마인더 메시지를 전송합니다.
    오늘 출석 체크에 ✅ 반응을 누른 멤버들에게 회고 모임 리마인더를 보냅니다.
    참여자가 없으면 안내 메시지를 전송합니다.

    Args:
        bot: Discord 봇 인스턴스
        channel_id: 메시지를 전송할 채널 ID
        role_id: 필터링할 역할 ID
    """
    try:
        channel = _get_channel(bot, channel_id)
        if not channel:
            return

        role = channel.guild.get_role(int(role_id))
        if not role:
            logger.error(f"Role not found: {role_id}")
            return

        message_ids = await repository.get_today_messages()
        if not message_ids:
            raise ValueError("No attendance messages found for today")

        latest_message_id = max(message_ids)
        logger.info(f"Using latest attendance message: {latest_message_id}")

        members = await _get_participated_members(channel, latest_message_id, role)

        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)
        await _send_reminder_or_empty(channel, members, voice_channel_id)

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise
