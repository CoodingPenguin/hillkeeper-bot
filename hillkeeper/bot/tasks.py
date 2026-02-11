"""task 스케쥴링 설정"""
import datetime
import logging
from discord.ext import tasks

from ..config import KST, THURSDAY, get_env
from ..attendance.service import send_morning_check, send_evening_reminder

logger = logging.getLogger('hillkeeper')


def _create_morning_check_task(bot):

    @tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
    async def morning_check():
        """
        매일 오전 9시에 실행되는 작업입니다.
        목요일에만 출석 체크 메시지를 전송합니다.
        """
        now = datetime.datetime.now(KST)
        if now.weekday() != THURSDAY:
            logger.info("Today is not Thursday, skipping morning check")
            return

        logger.info("Starting Thursday morning attendance check")

        channel_id = get_env('ATTENDANCE_CHANNEL_ID')
        role_id = get_env('RETROSPECTIVE_ROLE_ID')

        if not channel_id or not role_id:
            logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set")
            return

        await send_morning_check(bot, channel_id, role_id)

    @morning_check.error
    async def morning_check_error(error):
        logger.error(f"Morning check task failed: {error}")

    return morning_check


def _create_evening_reminder_task(bot):

    @tasks.loop(time=datetime.time(hour=21, minute=45, tzinfo=KST))
    async def evening_reminder():
        """
        매일 오후 9시 45분에 실행되는 작업입니다.
        목요일에만 회고 모임 리마인더를 전송합니다.
        """
        now = datetime.datetime.now(KST)
        if now.weekday() != THURSDAY:
            logger.info("Today is not Thursday, skipping evening reminder")
            return

        logger.info("Starting Thursday evening reminder")

        channel_id = get_env('ATTENDANCE_CHANNEL_ID')
        role_id = get_env('RETROSPECTIVE_ROLE_ID')

        if not channel_id or not role_id:
            logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set")
            return

        await send_evening_reminder(bot, channel_id, role_id)

    @evening_reminder.error
    async def evening_reminder_error(error):
        logger.error(f"Evening reminder task failed: {error}")

    return evening_reminder


def register_tasks(bot):
    """봇에 스케줄 작업을 등록합니다."""
    bot.morning_check = _create_morning_check_task(bot)
    bot.evening_reminder = _create_evening_reminder_task(bot)

    bot.morning_check.start()
    bot.evening_reminder.start()
    logger.info("Tasks started successfully")
