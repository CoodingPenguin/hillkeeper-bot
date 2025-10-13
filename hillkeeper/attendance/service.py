import logging

from ..config import EMOJI_CHECK, EMOJI_CROSS, get_env
from ..messages import create_morning_check_embed, create_evening_reminder_embed, create_no_participants_embed
from ..utils import get_users_who_reacted
from . import repository

logger = logging.getLogger('hillkeeper')


async def send_morning_check(bot, channel_id: str, role_id: str):
    """
    아침 출석 체크 메시지를 전송합니다.
    지정된 채널에 출석 체크 메시지를 보내고 ✅/❌ 이모지를 추가합니다.
    메시지 정보는 Redis에 7일간 보관됩니다.

    Args:
        bot: Discord 봇 인스턴스
        channel_id: 메시지를 전송할 채널 ID
        role_id: 멘션할 역할 ID
    """
    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel not found: {channel_id}")
            return

        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)
        content, embed = create_morning_check_embed(int(role_id), int(voice_channel_id))
        message = await channel.send(content=content, embed=embed)

        await message.add_reaction(EMOJI_CHECK)
        await message.add_reaction(EMOJI_CROSS)

        # Redis에 이벤트 저장 (7일 보관)
        await repository.save_event(
            message.id,
            channel_id=channel.id,
            role_id=int(role_id)
        )

        logger.info(f"Morning check message sent: {message.id}")

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
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel not found: {channel_id}")
            return

        guild = channel.guild
        role = guild.get_role(int(role_id))
        if not role:
            logger.error(f"Role not found: {role_id}")
            return

        # Redis에서 오늘 메시지 ID 가져오기
        message_ids = await repository.get_today_messages()

        # 참여한 멤버 수집
        participated_members = set()
        for message_id in message_ids:
            try:
                message = await channel.fetch_message(message_id)
                users = await get_users_who_reacted(
                    message,
                    EMOJI_CHECK,
                    exclude_bots=True,
                    filter_role=role
                )
                participated_members.update(users)

            except Exception as e:
                logger.error(f"Failed to fetch message {message_id}: {e}")
                # 실패한 메시지는 Redis에서 삭제
                await repository.delete_event(message_id)

        # 리마인더 메시지 전송
        voice_channel_id = get_env('VOICE_CHANNEL_ID', required=True)

        if participated_members:
            mentions = " ".join([member.mention for member in participated_members])
            content, embed = create_evening_reminder_embed(mentions, int(voice_channel_id))
            await channel.send(content=content, embed=embed)
            logger.info(f"Evening reminder sent to {len(participated_members)} members")
        else:
            embed = create_no_participants_embed()
            await channel.send(embed=embed)
            logger.info("No members checked in")

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise
