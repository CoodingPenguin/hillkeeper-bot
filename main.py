import logging
import os
import asyncio
import discord
from discord import app_commands
from aiohttp import web

from hillkeeper.config import get_env
from hillkeeper.bot.commands import register_commands
from hillkeeper.bot.events import register_events
from hillkeeper.bot.tasks import register_tasks
from hillkeeper.database.redis import redis_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('hillkeeper')


class HillkeeperBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """Initialize Redis connection and register scheduled tasks."""
        for attempt in range(1, 4):
            try:
                await redis_client.connect()
                break
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(f"Redis connection attempt {attempt}/3 failed: {e}, retrying in {wait}s...")
                await asyncio.sleep(wait)
        else:
            logger.error("Failed to connect to Redis after 3 attempts")

        register_tasks(self)


async def health_check(request):
    return web.Response(text='OK')


async def start_web_server() -> web.AppRunner:
    """
    Start a minimal web server for Render's port-binding requirement.

    Returns:
        The AppRunner instance for cleanup on shutdown.
    """
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)

    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f'Health check server started on port {port}')
    return runner


async def main_async():
    bot = HillkeeperBot()
    register_events(bot)
    register_commands(bot)

    runner = await start_web_server()

    token = get_env('DISCORD_TOKEN', required=True)
    logger.info('Starting bot...')
    try:
        await bot.start(token)
    finally:
        logger.info('Shutting down bot...')
        await bot.close()
        await redis_client.disconnect()
        if runner:
            await runner.cleanup()
        logger.info('Shutdown complete')


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
