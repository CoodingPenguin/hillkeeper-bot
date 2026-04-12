"""Slash command definitions."""
import logging
import discord

from ..config import get_env
from ..attendance.service import send_morning_check, send_evening_reminder

logger = logging.getLogger('hillkeeper')


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
