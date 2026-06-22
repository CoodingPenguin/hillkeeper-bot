"""Slash command definitions."""
import logging

import discord

from ..attendance.service import send_evening_reminder, send_morning_check
from ..config import get_env
from ..messages import create_schedule_skipped_embed, create_schedule_view_embed
from ..schedule import service as schedule_service

logger = logging.getLogger('hillkeeper')


def register_commands(bot):
    """Register slash commands on the bot."""

    @bot.tree.command(name="sync", description="슬래시 커맨드를 Discord에 동기화합니다.")
    async def sync(interaction: discord.Interaction):
        """Manually sync slash commands."""
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await bot.tree.sync()
            await interaction.followup.send(
                f"✅ Synced {len(synced)} command(s)", ephemeral=True
            )
            logger.info(
                f"Slash commands synced manually by {interaction.user}: "
                f"{len(synced)} commands"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: {e}", ephemeral=True)
            logger.error(f"Manual command sync failed: {e}")

    @bot.tree.command(name="ping", description="봇의 응답시간을 체크합니다.")
    async def ping(interaction: discord.Interaction):
        """Check bot response latency."""
        latency = round(bot.latency * 1000)
        logger.info(f'{interaction.user} used ping command. Latency: {latency}ms')
        await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

    @bot.tree.command(name="test_morning_check", description="회고모임 참석 메시지를 테스트합니다.")
    async def test_morning_check(interaction: discord.Interaction):
        """Send a test morning attendance check."""
        await interaction.response.defer(ephemeral=True)
        try:
            channel_id = get_env('TEST_CHANNEL_ID', required=True)
            role_id = get_env('TEST_ROLE_ID', required=True)
            await send_morning_check(bot, channel_id, role_id, is_test=True)
            await interaction.followup.send(
                "✅ Morning check test completed! Check the test channel.",
                ephemeral=True,
            )
            logger.info(f"{interaction.user} triggered test morning check")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test morning check failed: {e}")

    @bot.tree.command(name="test_evening_reminder", description="회고모임 리마인더 메시지를 테스트합니다.")
    async def test_evening_reminder(interaction: discord.Interaction):
        """Send a test evening reminder based on today's attendance data."""
        await interaction.response.defer(ephemeral=True)
        try:
            channel_id = get_env('TEST_CHANNEL_ID', required=True)
            role_id = get_env('TEST_ROLE_ID', required=True)
            await send_evening_reminder(bot, channel_id, role_id)
            await interaction.followup.send(
                "✅ Evening reminder test completed! Check the test channel.",
                ephemeral=True,
            )
            logger.info(f"{interaction.user} triggered test evening reminder")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test evening reminder failed: {e}")

    @bot.tree.command(name="schedule", description="다가오는 회고 모임 일정을 확인합니다.")
    async def schedule_view(interaction: discord.Interaction):
        """View the next meeting schedule."""
        await interaction.response.defer(ephemeral=True)
        try:
            meeting = await schedule_service.get_next_meeting()
            embed = create_schedule_view_embed(
                date=meeting["date"],
                day_name=meeting["day_name"],
                hour=meeting["hour"],
                minute=meeting["minute"],
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Schedule view failed: {e}")

    @bot.tree.command(name="skip", description="다가오는 회고 모임을 취소합니다.")
    async def skip(interaction: discord.Interaction):
        """Cancel the next meeting."""
        role_id = int(get_env('RETROSPECTIVE_ROLE_ID', required=True))
        if interaction.user.get_role(role_id) is None:
            await interaction.response.send_message(
                "❌ `@회고` 역할이 필요합니다.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            meeting = await schedule_service.skip_next_meeting(
                user_id=interaction.user.id
            )
            embed = create_schedule_skipped_embed(
                date=meeting["date"], day_name=meeting["day_name"]
            )
            await interaction.channel.send(embed=embed)
            await interaction.followup.send(
                "✅ 다가오는 모임이 취소되었습니다.", ephemeral=True
            )
            logger.info(
                f"{interaction.user.display_name} skipped meeting on "
                f"{meeting['date']}"
            )
        except Exception as e:
            await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}", ephemeral=True)
            logger.error(f"Schedule skip failed: {e}")
