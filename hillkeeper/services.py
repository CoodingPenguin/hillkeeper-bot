"""비즈니스 로직 모듈"""
import logging

from .config import EMOJI_CHECK, EMOJI_CROSS
from .messages import MESSAGE_MORNING_CHECK, MESSAGE_EVENING_REMINDER, MESSAGE_NO_PARTICIPANTS
from .utils import get_users_who_reacted

logger = logging.getLogger('hillkeeper-bot')

# 참여 체크 메시지 저장 (메시지 ID -> 메시지 객체)
attendance_messages = {}


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

        attendance_messages[message.id] = message
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

        # 참여한 멤버 수집
        participated_members = set()
        for message_id in list(attendance_messages.keys()):
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
                if message_id in attendance_messages:
                    del attendance_messages[message_id]

        # 리마인더 메시지 전송
        if participated_members:
            mentions = " ".join([member.mention for member in participated_members])
            await channel.send(MESSAGE_EVENING_REMINDER.format(mentions=mentions))
            logger.info(f"Evening reminder sent to {len(participated_members)} members")
        else:
            await channel.send(MESSAGE_NO_PARTICIPANTS)
            logger.info("No members checked in")

        attendance_messages.clear()

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise
