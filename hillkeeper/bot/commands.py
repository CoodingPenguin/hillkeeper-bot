"""Slash command definitions."""
import datetime
import logging

import discord
from discord import app_commands

from ..config import (
    KST, DAY_NAMES_REVERSE, REMINDER_LEAD_MINUTES,
    DEFAULT_MEETING_HOUR, DEFAULT_MEETING_MINUTE, get_env,
)
from ..attendance.service import send_morning_check, send_evening_reminder
from ..schedule import service as schedule_service
from ..schedule import repository as schedule_repository
from ..messages import (
    create_schedule_changed_embed,
    create_schedule_skipped_embed,
    create_default_changed_embed,
    create_schedule_view_embed,
)

logger = logging.getLogger('hillkeeper')

DAY_CHOICES = [
    app_commands.Choice(name="월요일", value=0),
    app_commands.Choice(name="화요일", value=1),
    app_commands.Choice(name="수요일", value=2),
    app_commands.Choice(name="목요일", value=3),
    app_commands.Choice(name="금요일", value=4),
    app_commands.Choice(name="토요일", value=5),
    app_commands.Choice(name="일요일", value=6),
]


def _parse_time(time_str: str) -> tuple[int, int]:
    """
    Parse HH:MM time string into (hour, minute) tuple.

    Args:
        time_str: Time string in HH:MM format.

    Returns:
        (hour, minute) tuple.

    Raises:
        ValueError: If the format is invalid.
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError()
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError()
        return hour, minute
    except (ValueError, IndexError):
        raise ValueError(f"시간 형식이 올바르지 않습니다: {time_str} (HH:MM 형식으로 입력해주세요)")


def _calculate_reminder_time(*, hour: int, minute: int) -> datetime.time:
    """Calculate the reminder time (15 min before meeting)."""
    meeting = datetime.datetime(2000, 1, 1, hour, minute)
    reminder = meeting - datetime.timedelta(minutes=REMINDER_LEAD_MINUTES)
    return datetime.time(hour=reminder.hour, minute=reminder.minute, tzinfo=KST)


async def _update_today_evening_reminder(bot, weekday: int, hour: int, minute: int):
    """
    If the changed schedule affects today, update the evening reminder timer.

    Args:
        bot: The Discord bot instance.
        weekday: The weekday of the changed schedule.
        hour: Meeting hour.
        minute: Meeting minute.
    """
    today = datetime.datetime.now(KST).date()
    if today.weekday() == weekday:
        reminder_time = _calculate_reminder_time(hour=hour, minute=minute)
        if hasattr(bot, 'evening_reminder'):
            bot.evening_reminder.change_interval(time=reminder_time)
            logger.info(f"Updated today's evening reminder to {reminder_time.hour:02d}:{reminder_time.minute:02d}")


class RescheduleGroup(app_commands.Group):
    """Slash command group for rescheduling meetings."""

    def __init__(self):
        super().__init__(
            name="reschedule",
            description="회고 모임 일정을 변경합니다.",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check that the user has the retrospective role."""
        role_id = int(get_env('RETROSPECTIVE_ROLE_ID', required=True))
        if interaction.user.get_role(role_id) is None:
            await interaction.response.send_message(
                "❌ `@회고` 역할이 필요합니다.", ephemeral=True
            )
            return False
        return True

    @app_commands.command(name="once", description="이번 주만 다른 요일/시간으로 변경")
    @app_commands.describe(day="요일", time="모임 시간 (HH:MM)")
    @app_commands.choices(day=DAY_CHOICES)
    async def once(
        self, interaction: discord.Interaction,
        day: app_commands.Choice[int], time: str,
    ):
        """Reschedule this week's meeting to a different day/time."""
        await interaction.response.defer(ephemeral=True)

        try:
            hour, minute = _parse_time(time)
            message = await schedule_service.reschedule_once(
                weekday=day.value, hour=hour, minute=minute,
                user_id=interaction.user.id,
            )

            await _update_today_evening_reminder(
                interaction.client, day.value, hour, minute
            )

            day_name = DAY_NAMES_REVERSE[day.value]
            _, embed = create_schedule_changed_embed(
                day_name=day_name, hour=hour, minute=minute
            )
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ 일정이 변경되었습니다.", ephemeral=True)

            logger.info(f"{interaction.user.display_name} rescheduled once: {day.name} {time}")

        except ValueError as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Reschedule once failed: {e}")

    @app_commands.command(name="default", description="기본 요일/시간을 영구 변경")
    @app_commands.describe(day="요일", time="모임 시간 (HH:MM)")
    @app_commands.choices(day=DAY_CHOICES)
    async def default(
        self, interaction: discord.Interaction,
        day: app_commands.Choice[int], time: str,
    ):
        """Change the permanent default meeting schedule."""
        await interaction.response.defer(ephemeral=True)

        try:
            hour, minute = _parse_time(time)
            message = await schedule_service.reschedule_default(
                weekday=day.value, hour=hour, minute=minute,
                user_id=interaction.user.id,
            )

            day_name = DAY_NAMES_REVERSE[day.value]
            _, embed = create_default_changed_embed(
                day_name=day_name, hour=hour, minute=minute
            )
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ 기본 일정이 변경되었습니다.", ephemeral=True)

            logger.info(f"{interaction.user.display_name} changed default: {day.name} {time}")

        except ValueError as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Reschedule default failed: {e}")

    @app_commands.command(name="skip", description="이번 주 모임 취소")
    async def skip(self, interaction: discord.Interaction):
        """Cancel this week's meeting."""
        await interaction.response.defer(ephemeral=True)

        try:
            message = await schedule_service.skip_this_week(
                user_id=interaction.user.id,
            )

            current = await schedule_service.get_current_schedule()
            day_name = current["day_name"]

            _, embed = create_schedule_skipped_embed(day_name=day_name)
            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ 이번 주 모임이 취소되었습니다.", ephemeral=True)

            logger.info(f"{interaction.user.display_name} skipped this week")

        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Reschedule skip failed: {e}")


def register_commands(bot):
    """Register slash commands on the bot."""

    @bot.tree.command(name="sync", description="Sync slash commands to Discord.")
    async def sync(interaction: discord.Interaction):
        """Manually sync slash commands."""
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await bot.tree.sync()
            await interaction.followup.send(
                f"✅ Synced {len(synced)} command(s)",
                ephemeral=True
            )
            logger.info(f"Slash commands synced manually by {interaction.user}: {len(synced)} commands")
        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)
            logger.error(f"Manual command sync failed: {e}")

    @bot.tree.command(name="ping", description="Check bot latency.")
    async def ping(interaction: discord.Interaction):
        """Check bot response latency."""
        latency = round(bot.latency * 1000)
        logger.info(f'{interaction.user} used ping command. Latency: {latency}ms')
        await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

    @bot.tree.command(name="test_morning_check", description="Test morning attendance message. Auto-deletes in 1 min.")
    async def test_morning_check(interaction: discord.Interaction):
        """Send a test morning attendance check."""
        await interaction.response.defer(ephemeral=True)

        try:
            channel_id = get_env('TEST_CHANNEL_ID', required=True)
            role_id = get_env('TEST_ROLE_ID', required=True)

            await send_morning_check(bot, channel_id, role_id, is_test=True)
            await interaction.followup.send(
                "✅ Morning check test completed! Check the test channel. (Auto-delete in 1 minute)",
                ephemeral=True
            )
            logger.info(f"{interaction.user} triggered test morning check")

        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test morning check failed: {e}")

    @bot.tree.command(name="test_evening_reminder", description="Test evening reminder message.")
    async def test_evening_reminder(interaction: discord.Interaction):
        """Send a test evening reminder based on today's attendance data."""
        await interaction.response.defer(ephemeral=True)

        try:
            channel_id = get_env('TEST_CHANNEL_ID', required=True)
            role_id = get_env('TEST_ROLE_ID', required=True)

            await send_evening_reminder(bot, channel_id, role_id)
            await interaction.followup.send(
                "✅ Evening reminder test completed! Check the test channel.",
                ephemeral=True
            )
            logger.info(f"{interaction.user} triggered test evening reminder")

        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test evening reminder failed: {e}")

    @bot.tree.command(name="schedule", description="현재 회고 모임 일정을 확인합니다.")
    async def schedule_view(interaction: discord.Interaction):
        """View the current meeting schedule."""
        await interaction.response.defer(ephemeral=True)

        try:
            current = await schedule_service.get_current_schedule()

            override_text = None
            if "override" in current:
                override = current["override"]
                if override.is_skip:
                    override_text = "이번 주 모임 취소됨"
                else:
                    override_day = DAY_NAMES_REVERSE.get(
                        datetime.date.fromisoformat(override.date).weekday(),
                        override.date,
                    )
                    override_text = f"{override_day} {override.hour:02d}:{override.minute:02d}로 변경됨"

            embed = create_schedule_view_embed(
                day_name=current["day_name"],
                hour=current["hour"],
                minute=current["minute"],
                override_text=override_text,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Schedule view failed: {e}")

    # Register the reschedule command group
    bot.tree.add_command(RescheduleGroup())
