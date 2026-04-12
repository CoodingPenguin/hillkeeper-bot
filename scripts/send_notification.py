#!/usr/bin/env python3
"""
Manual notification sender.

Usage:
  $ python scripts/send_notification.py morning
  $ python scripts/send_notification.py evening

Note:
  - Sends to the real ATTENDANCE_CHANNEL.
  - Press Ctrl+C to force-quit if the bot does not exit.
"""
import asyncio
import sys
import discord
from discord.ext import commands

from hillkeeper.config import get_env
from hillkeeper.attendance.service import send_morning_check, send_evening_reminder
from hillkeeper.database.redis import redis_client


async def main(notification_type: str):
    """Send a notification manually."""
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f'Bot connected as {bot.user}')

        try:
            await redis_client.connect()
            print('Redis connected')

            channel_id = get_env('ATTENDANCE_CHANNEL_ID', required=True)
            role_id = get_env('RETROSPECTIVE_ROLE_ID', required=True)

            if notification_type == 'morning':
                print(f'Sending morning check to channel {channel_id}...')
                await send_morning_check(bot, channel_id, role_id, is_test=False)
                print('✅ Morning check sent successfully!')
            elif notification_type == 'evening':
                print(f'Sending evening reminder to channel {channel_id}...')
                await send_evening_reminder(bot, channel_id, role_id)
                print('✅ Evening reminder sent successfully!')

        except Exception as e:
            print(f'❌ Error: {e}')
        finally:
            await redis_client.close()
            await bot.close()

    token = get_env('DISCORD_TOKEN', required=True)
    await bot.start(token)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['morning', 'evening']:
        print('Usage: python scripts/send_notification.py [morning|evening]')
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
