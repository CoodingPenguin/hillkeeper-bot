"""slash 명령어 설정"""
import logging
import discord

from ..config import get_env
from ..attendance.service import send_morning_check, send_evening_reminder

logger = logging.getLogger('hillkeeper')


def register_commands(bot):
    """봇에 slash commands를 등록합니다."""

    @bot.tree.command(name="sync", description="슬래시 커맨드를 Discord에 동기화합니다.")
    async def sync(interaction: discord.Interaction):
        """슬래시 커맨드를 수동으로 동기화합니다."""
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

    @bot.tree.command(name="ping", description="봇의 응답시간을 체크합니다.")
    async def ping(interaction: discord.Interaction):
        """봇의 응답 속도를 확인합니다."""
        latency = round(bot.latency * 1000)
        logger.info(f'{interaction.user} used ping command. Latency: {latency}ms')
        await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')

    @bot.tree.command(name="test_morning_check", description="회고모임 참석 메시지를 테스트합니다. 1분 후 자동 삭제됩니다.")
    async def test_morning_check(interaction: discord.Interaction):
        """아침 출석 체크를 테스트합니다."""
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

    @bot.tree.command(name="test_evening_reminder", description="회고모임 리마인드 메시지를 테스트합니다.")
    async def test_evening_reminder(interaction: discord.Interaction):
        """
        저녁 리마인더를 테스트합니다.
        오늘의 출석 데이터를 기반으로 리마인더 메시지를 전송합니다.
        """
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
