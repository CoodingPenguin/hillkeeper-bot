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

# 로깅 설정
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
        """봇 시작 시 초기화 작업을 수행합니다."""
        # Redis 연결
        await redis_client.connect()

        try:
            # slash command 동기화
            await self.tree.sync()
            logger.info("Slash commands synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # 태스크 스케쥴링 등록
        register_tasks(self)


async def health_check(request):
    return web.Response(text='OK')


async def start_web_server():
    """Render 포트 바인딩을 위한 웹 서버"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)

    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f'Health check server started on port {port}')


async def main_async():
    # 봇 인스턴스 생성
    bot = HillkeeperBot()

    # 이벤트 핸들러 등록
    register_events(bot)

    # 명령어 등록
    register_commands(bot)

    # 웹 서버 시작 (Render 포트 바인딩용)
    await start_web_server()

    # 봇 실행
    token = get_env('DISCORD_TOKEN', required=True)
    logger.info('Starting bot...')
    await bot.start(token)


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
