"""이벤트 핸들러 모듈"""
import logging

logger = logging.getLogger('hillkeeper-bot')


def register_events(bot, attendance_messages: dict):
    """봇에 이벤트 핸들러를 등록합니다."""

    @bot.event
    async def on_ready():
        """봇이 준비되었을 때 실행됩니다."""
        logger.info(f'Bot is ready: {bot.user}')
        logger.info(f'Bot ID: {bot.user.id}')

    @bot.event
    async def on_raw_reaction_add(payload):
        """이모지 반응이 추가될 때 실행됩니다."""
        if payload.user_id == bot.user.id:
            return

        if payload.message_id not in attendance_messages:
            return

        logger.info(f"User {payload.user_id} reacted with {payload.emoji} to attendance check")
