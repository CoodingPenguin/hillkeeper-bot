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
        await on_attendance_reaction(payload)
        # 필요시 다른 reaction handler 추가 가능
        # await on_another_reaction(payload)

    async def on_attendance_reaction(payload):
        """
        출석 체크 메시지에 대한 이모지 반응을 처리합니다.
        하나만 선택 가능하도록 반대쪽 이모지는 자동으로 제거합니다.
        """
        if payload.user_id == bot.user.id:
            return

        # ✅ 또는 ❌ 반응만 처리
        if str(payload.emoji) not in [EMOJI_CHECK, EMOJI_CROSS]:
            return

        # 출석 체크 메시지인지 확인 (Redis에 저장된 이벤트인지 체크)
        event = await repository.get_event(payload.message_id)
        if not event:
            # 출석 체크 메시지가 아니면 무시
            return

        # 사용자 정보 가져오기
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            return

        # 메시지 가져오기
        try:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
        except Exception as e:
            logger.error(f"Failed to fetch message {payload.message_id}: {e}")
            return

        # 반대쪽 이모지 제거 (하나만 선택 가능)
        opposite_emoji = EMOJI_CROSS if str(payload.emoji) == EMOJI_CHECK else EMOJI_CHECK
        try:
            await message.remove_reaction(opposite_emoji, member)
        except Exception as e:
            # 반대쪽 이모지가 없거나 권한 문제 등으로 제거 실패 시 무시
            logger.debug(f"Failed to remove opposite reaction: {e}")

        # Redis에 응답 저장
        response = "yes" if str(payload.emoji) == EMOJI_CHECK else "no"
        await repository.save_response(
            payload.message_id,
            payload.user_id,
            username=member.display_name,
            response=response
        )

        logger.info(f"User {member.display_name} ({payload.user_id}) reacted with {payload.emoji}")

