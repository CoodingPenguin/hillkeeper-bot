"""출석 비즈니스 로직 모듈"""
import logging

from ..config import EMOJI_CHECK, EMOJI_CROSS
from ..messages import MESSAGE_MORNING_CHECK, MESSAGE_EVENING_REMINDER, MESSAGE_NO_PARTICIPANTS
from ..utils import get_users_who_reacted
from . import repository

logger = logging.getLogger('hillkeeper')


async def send_morning_check(bot, channel_id: str, role_id: str):
    """아침 출석 체크 메시지를 전송합니다."""
    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel not found: {channel_id}")
            return

        message_text = MESSAGE_MORNING_CHECK.format(role_id=role_id)
        message = await channel.send(message_text)

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
    """저녁 리마인더 메시지를 전송합니다."""
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
        if participated_members:
            mentions = " ".join([member.mention for member in participated_members])
            await channel.send(MESSAGE_EVENING_REMINDER.format(mentions=mentions))
            logger.info(f"Evening reminder sent to {len(participated_members)} members")
        else:
            await channel.send(MESSAGE_NO_PARTICIPANTS)
            logger.info("No members checked in")

        # 오늘 이벤트는 유지 (7일 보관)
        # clear_today_events() 호출 안 함

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise
