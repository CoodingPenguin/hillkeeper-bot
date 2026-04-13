"""Scheduled task definitions."""
import datetime
import logging
from discord.ext import tasks

from ..config import KST, DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE, calculate_reminder_time, get_env
from ..attendance.service import send_morning_check, send_evening_reminder
from ..schedule import repository as schedule_repository

logger = logging.getLogger('hillkeeper')


async def _run_scheduled_task(task_name: str, service_fn, bot, *, schedule=None):
    """
    Guard logic for scheduled tasks. Checks Redis for today's schedule
    and validates required environment variables before calling the
    service function.

    Args:
        task_name: Human-readable name used in log messages.
        service_fn: Async service function to invoke.
        bot: The Discord bot instance.
        schedule: Pre-fetched schedule tuple, or None to fetch from Redis.
    """
    if schedule is None:
        now = datetime.datetime.now(KST)
        schedule = await schedule_repository.get_effective_schedule_for_date(now.date())

    if schedule is None:
        logger.info(f"No meeting scheduled today, skipping {task_name}")
        return

    logger.info(f"Starting {task_name}")

    channel_id = get_env('ATTENDANCE_CHANNEL_ID')
    role_id = get_env('RETROSPECTIVE_ROLE_ID')

    if not channel_id or not role_id:
        logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set")
        return

    await service_fn(bot, channel_id, role_id)


def _create_morning_check_task(bot):

    @tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
    async def morning_check():
        """Run daily at 09:00 KST. Check Redis and update evening reminder."""
        now = datetime.datetime.now(KST)
        schedule = await schedule_repository.get_effective_schedule_for_date(now.date())

        if schedule is not None:
            hour, minute = schedule
            reminder_time = calculate_reminder_time(hour=hour, minute=minute)
            bot.evening_reminder.change_interval(time=reminder_time)
            logger.info(f"Evening reminder set to {reminder_time.hour:02d}:{reminder_time.minute:02d}")

        await _run_scheduled_task("morning attendance check", send_morning_check, bot, schedule=schedule)

    @morning_check.error
    async def morning_check_error(error):
        logger.error(f"Morning check task failed: {error}")

    return morning_check


def _create_evening_reminder_task(bot):

    default_reminder = calculate_reminder_time(
        hour=DEFAULT_MEETING_HOUR, minute=DEFAULT_MEETING_MINUTE
    )

    @tasks.loop(time=default_reminder)
    async def evening_reminder():
        """Run daily at dynamically-set time. Send reminder if meeting today."""
        await _run_scheduled_task("evening reminder", send_evening_reminder, bot)

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


async def initialize_task_schedule(bot):
    """
    Read the default schedule from Redis and set the evening
    reminder time accordingly. Called once on bot startup.

    Args:
        bot: The Discord bot instance.
    """
    default = await schedule_repository.get_default()
    if default is None:
        logger.info("No custom default schedule, using hardcoded times")
        return

    reminder_time = calculate_reminder_time(hour=default.hour, minute=default.minute)
    bot.evening_reminder.change_interval(time=reminder_time)
    logger.info(
        f"Initialized evening reminder to {reminder_time.hour:02d}:{reminder_time.minute:02d} "
        f"(meeting at {default.hour:02d}:{default.minute:02d})"
    )
