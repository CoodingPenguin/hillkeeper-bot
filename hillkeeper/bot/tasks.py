"""task 스케쥴링 설정"""
import datetime
import logging
from discord.ext import tasks

from ..config import KST, THURSDAY, get_env
from ..attendance.service import send_morning_check, send_evening_reminder

logger = logging.getLogger('hillkeeper')


def _is_thursday() -> bool:
    """
    현재 요일이 목요일인지 확인합니다.

    Returns:
        목요일이면 True, 아니면 False
    """
    now = datetime.datetime.now(KST)
    return now.weekday() == THURSDAY


async def _run_thursday_task(task_name: str, service_fn, bot):
    """
    목요일에만 실행되는 작업의 공통 로직을 처리합니다.

    Args:
        task_name: 작업 이름 (로그용)
        service_fn: 실행할 서비스 함수
        bot: Discord 봇 인스턴스
    """
    if not _is_thursday():
        logger.info(f"Today is not Thursday, skipping {task_name}")
        return

    logger.info(f"Starting Thursday {task_name}")

    channel_id = get_env('ATTENDANCE_CHANNEL_ID')
    role_id = get_env('RETROSPECTIVE_ROLE_ID')

    if not channel_id or not role_id:
        logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set")
        return

    await service_fn(bot, channel_id, role_id)


def _create_morning_check_task(bot):

    @tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
    async def morning_check():
        """매일 오전 9시에 실행되는 작업입니다."""
        await _run_thursday_task("morning attendance check", send_morning_check, bot)

    @morning_check.error
    async def morning_check_error(error):
        logger.error(f"Morning check task failed: {error}")

    return morning_check


def _create_evening_reminder_task(bot):

    @tasks.loop(time=datetime.time(hour=21, minute=45, tzinfo=KST))
    async def evening_reminder():
        """매일 오후 9시 45분에 실행되는 작업입니다."""
        await _run_thursday_task("evening reminder", send_evening_reminder, bot)

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
