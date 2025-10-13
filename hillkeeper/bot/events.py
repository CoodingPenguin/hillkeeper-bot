"""discord 이벤트 핸들러"""
import logging

from ..config import EMOJI_CHECK, EMOJI_CROSS
from ..attendance import repository

logger = logging.getLogger('hillkeeper')


def register_events(bot):
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

        # ✅ 또는 ❌ 반응만 처리
        if str(payload.emoji) not in [EMOJI_CHECK, EMOJI_CROSS]:
            return

        # 사용자 정보 가져오기
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        # Redis에 응답 저장
        response = "yes" if str(payload.emoji) == EMOJI_CHECK else "no"
        await repository.save_response(
            payload.message_id,
            payload.user_id,
            username=member.display_name,
            response=response
        )

        logger.info(f"User {member.display_name} ({payload.user_id}) reacted with {payload.emoji}")
