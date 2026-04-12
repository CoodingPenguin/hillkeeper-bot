"""Scheduled task definitions."""
import datetime
import logging
from discord.ext import tasks

from ..config import KST, THURSDAY, get_env
from ..attendance.service import send_morning_check, send_evening_reminder

logger = logging.getLogger('hillkeeper')


def _is_thursday() -> bool:
    """Return True if today is Thursday in KST."""
    now = datetime.datetime.now(KST)
    return now.weekday() == THURSDAY


async def _run_thursday_task(task_name: str, service_fn, bot):
    """
    Shared guard logic for Thursday-only scheduled tasks.

    Skips execution on non-Thursday days and validates that
    required environment variables are set before calling
    the service function.

    Args:
        task_name: Human-readable name used in log messages.
        service_fn: Async service function to invoke.
        bot: The Discord bot instance.
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
        """Run daily at 09:00 KST."""
        await _run_thursday_task("morning attendance check", send_morning_check, bot)

    @morning_check.error
    async def morning_check_error(error):
        logger.error(f"Morning check task failed: {error}")

    return morning_check


def _create_evening_reminder_task(bot):

    @tasks.loop(time=datetime.time(hour=21, minute=45, tzinfo=KST))
    async def evening_reminder():
        """Run daily at 21:45 KST."""
        await _run_thursday_task("evening reminder", send_evening_reminder, bot)

    @evening_reminder.error
    async def evening_reminder_error(error):
        logger.error(f"Evening reminder task failed: {error}")

    return evening_reminder


def register_tasks(bot):
    """Register and start all scheduled tasks."""
    bot.morning_check = _create_morning_check_task(bot)
    bot.evening_reminder = _create_evening_reminder_task(bot)

    bot.morning_check.start()
    bot.evening_reminder.start()
    logger.info("Tasks started successfully")
