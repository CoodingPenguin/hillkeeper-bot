"""slash 명령어 설정"""
import logging
import discord

from ..config import get_env
from ..attendance.service import send_morning_check, send_evening_reminder, clear_today_attendance

logger = logging.getLogger('hillkeeper')


def register_commands(bot):
    """봇에 slash commands를 등록합니다."""

    @bot.tree.command(name="ping", description="Check bot's response time")
    async def ping(interaction: discord.Interaction):
        """봇의 응답 속도를 확인합니다."""
        latency = round(bot.latency * 1000)
        logger.info(f'{interaction.user} used ping command. Latency: {latency}ms')
        await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

    @bot.tree.command(name="test_morning_check", description="Test morning attendance check")
    async def test_morning_check(interaction: discord.Interaction):
        """아침 출석 체크를 테스트합니다."""
        await interaction.response.defer(ephemeral=True)

        try:
            channel_id = get_env('TEST_CHANNEL_ID') or get_env('ATTENDANCE_CHANNEL_ID')
            role_id = get_env('RETROSPECTIVE_ROLE_ID')

            if not channel_id or not role_id:
                await interaction.followup.send(
                    "❌ Required environment variables not set",
                    ephemeral=True
                )
                return

            await send_morning_check(bot, channel_id, role_id)
            await interaction.followup.send(
                "✅ Morning check test completed! Check the test channel.",
                ephemeral=True
            )
            logger.info(f"{interaction.user} triggered test morning check")

        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test morning check failed: {e}")

    @bot.tree.command(name="test_evening_reminder", description="Test evening reminder")
    async def test_evening_reminder(interaction: discord.Interaction):
        """
        저녁 리마인더를 테스트합니다.
        오늘의 출석 데이터를 기반으로 리마인더 메시지를 전송합니다.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            channel_id = get_env('TEST_CHANNEL_ID') or get_env('ATTENDANCE_CHANNEL_ID')
            role_id = get_env('RETROSPECTIVE_ROLE_ID')

            if not channel_id or not role_id:
                await interaction.followup.send(
                    "❌ Required environment variables not set",
                    ephemeral=True
                )
                return

            await send_evening_reminder(bot, channel_id, role_id)
            await interaction.followup.send(
                "✅ Evening reminder test completed! Check the test channel.",
                ephemeral=True
            )
            logger.info(f"{interaction.user} triggered test evening reminder")

        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Test evening reminder failed: {e}")

    @bot.tree.command(name="clear_today_attendance", description="Clear today's attendance data (for testing)")
    async def clear_today_attendance_command(interaction: discord.Interaction):
        """
        오늘의 출석 데이터를 초기화합니다.
        테스트 목적으로 사용됩니다.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            await clear_today_attendance()
            await interaction.followup.send(
                "✅ 오늘의 출석 데이터를 초기화했습니다.",
                ephemeral=True
            )
            logger.info(f"{interaction.user} cleared today's attendance data")

        except Exception as e:
            await interaction.followup.send(f"❌ Failed: {e}", ephemeral=True)
            logger.error(f"Clear today attendance failed: {e}")
