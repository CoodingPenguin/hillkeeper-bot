"""언덕지기 봇 메인 진입점"""
import logging
import discord
from discord import app_commands

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
logger = logging.getLogger('hillkeeper-bot')


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
            await self.tree.sync()
            logger.info("Slash commands synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        register_tasks(self)


def main():
    # 봇 인스턴스 생성
    bot = HillkeeperBot()

    # 이벤트 핸들러 등록 (Redis 기반으로 변경되어 attendance_messages는 불필요)
    register_events(bot, {})

    # 명령어 등록
    register_commands(bot)

    # 봇 실행
    token = get_env('DISCORD_TOKEN', required=True)
    logger.info('Starting bot...')
    bot.run(token)


if __name__ == '__main__':
    main()
