import os
import logging
import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('hillkeeper-bot')

# 환경 변수 로드
load_dotenv()

# 한국 시간대 설정
KST = ZoneInfo("Asia/Seoul")

# 참여 체크 메시지 저장 (메시지 ID -> 메시지 객체)
attendance_messages = {}


class HillkeeperBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # 역할 멤버 목록 확인에 필요
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """봇 시작 시 slash commands를 동기화합니다."""
        try:
            await self.tree.sync()
            logger.info("Slash commands synced successfully")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # 스케줄러 시작
        self.morning_check.start()
        self.evening_reminder.start()
        logger.info("Scheduled tasks started")


bot = HillkeeperBot()


@bot.event
async def on_ready():
    logger.info(f'Bot is ready: {bot.user}')
    logger.info(f'Bot ID: {bot.user.id}')


async def send_morning_check(channel_id: str, role_id: str):
    """아침 출석 체크 메시지를 전송합니다."""
    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel not found: {channel_id}")
            return

        # '@회고' 역할 멘션하여 메시지 전송
        message = await channel.send(
            f"<@&{role_id}> 안녕하세요! 오늘 저녁 10시 회고 모임 참여 여부를 체크해주세요.\n"
            f"✅ 참여\n"
            f"❌ 불참"
        )

        # 이모지 반응 추가
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        # 메시지 저장
        attendance_messages[message.id] = message

        logger.info(f"Morning check message sent: {message.id}")

    except Exception as e:
        logger.error(f"Failed to send morning check message: {e}")
        raise


@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=KST))
async def morning_check():
    """매일 오전 9시에 실행되는 작업입니다."""
    # 목요일(3)인지 확인
    now = datetime.datetime.now(KST)
    if now.weekday() != 3:  # 0=월요일, 3=목요일
        logger.info(f"Today is not Thursday, skipping morning check (weekday: {now.weekday()})")
        return

    logger.info("Starting Thursday morning attendance check")

    # 환경 변수에서 채널 ID와 역할 ID 가져오기
    channel_id = os.getenv('ATTENDANCE_CHANNEL_ID')
    role_id = os.getenv('RETROSPECTIVE_ROLE_ID')

    if not channel_id or not role_id:
        logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set in environment variables")
        return

    await send_morning_check(channel_id, role_id)


# 스케줄러를 봇 메서드로 바인딩
bot.morning_check = morning_check


async def send_evening_reminder(channel_id: str, role_id: str):
    """저녁 리마인더 메시지를 전송합니다."""
    try:
        channel = bot.get_channel(int(channel_id))
        if not channel:
            logger.error(f"Channel not found: {channel_id}")
            return

        # 오늘 아침에 보낸 메시지들을 찾아서 반응 확인
        guild = channel.guild
        role = guild.get_role(int(role_id))
        if not role:
            logger.error(f"Role not found: {role_id}")
            return

        # 역할을 가진 모든 멤버
        all_members = set(role.members)
        participated_members = set()

        # 참여 체크 메시지의 반응 확인
        for message_id, message in list(attendance_messages.items()):
            try:
                # 메시지를 다시 fetch하여 최신 반응 정보 가져오기
                message = await channel.fetch_message(message_id)

                for reaction in message.reactions:
                    if str(reaction.emoji) == "✅":
                        # ✅ 반응한 사용자 목록 가져오기
                        async for user in reaction.users():
                            if user.id != bot.user.id:  # 봇 제외
                                member = guild.get_member(user.id)
                                if member and member in all_members:
                                    participated_members.add(member)

            except discord.NotFound:
                logger.warning(f"Message {message_id} not found, removing from tracking")
                del attendance_messages[message_id]
            except Exception as e:
                logger.error(f"Failed to fetch message {message_id}: {e}")

        # 참여한 멤버 멘션
        if participated_members:
            # 참여한 멤버들 멘션
            mentions = " ".join([member.mention for member in participated_members])
            await channel.send(
                f"{mentions} 10시 회고 모임이 곧 시작됩니다. 음성 채널로 들어와 주세요! 🎤"
            )
            logger.info(f"Evening reminder sent to {len(participated_members)} participating members")
        else:
            await channel.send("아무도 참여 체크를 하지 않으셨네요. 😢")
            logger.info("No members checked in")

        # 오늘의 참여 체크 메시지 정리
        attendance_messages.clear()

    except Exception as e:
        logger.error(f"Failed to send evening reminder: {e}")
        raise


@tasks.loop(time=datetime.time(hour=21, minute=45, tzinfo=KST))
async def evening_reminder():
    """매일 오후 9시 45분에 실행되는 작업입니다."""
    # 목요일(3)인지 확인
    now = datetime.datetime.now(KST)
    if now.weekday() != 3:  # 0=월요일, 3=목요일
        logger.info(f"Today is not Thursday, skipping evening reminder (weekday: {now.weekday()})")
        return

    logger.info("Starting Thursday evening reminder")

    # 환경 변수에서 채널 ID와 역할 ID 가져오기
    channel_id = os.getenv('ATTENDANCE_CHANNEL_ID')
    role_id = os.getenv('RETROSPECTIVE_ROLE_ID')

    if not channel_id or not role_id:
        logger.error("ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set in environment variables")
        return

    await send_evening_reminder(channel_id, role_id)


# 스케줄러를 봇 메서드로 바인딩
bot.evening_reminder = evening_reminder


@bot.event
async def on_raw_reaction_add(payload):
    """이모지 반응이 추가될 때 실행됩니다."""
    # 봇 자신의 반응은 무시
    if payload.user_id == bot.user.id:
        return

    # 참여 체크 메시지에 대한 반응인지 확인
    if payload.message_id not in attendance_messages:
        return

    # ✅ 또는 ❌ 반응만 처리
    if str(payload.emoji) not in ["✅", "❌"]:
        return

    logger.info(f"User {payload.user_id} reacted with {payload.emoji} to attendance check")


@bot.tree.command(name="ping", description="Check bot's response time")
async def ping(interaction: discord.Interaction):
    """봇의 응답 속도를 확인합니다."""
    latency = round(bot.latency * 1000)
    logger.info(f'{interaction.user} used ping command. Latency: {latency}ms')
    await interaction.response.send_message(f'🏓 Pong! Latency: {latency}ms')


@bot.tree.command(name="test", description="Simple test command")
async def test_cmd(interaction: discord.Interaction):
    """간단한 테스트 명령어입니다."""
    await interaction.response.send_message("✅ Test command works!")


@bot.tree.command(name="test_morning_check", description="Test morning attendance check")
async def test_morning_check(interaction: discord.Interaction):
    """아침 출석 체크를 테스트합니다."""
    await interaction.response.defer(ephemeral=True)

    try:
        # 테스트용 채널 ID와 역할 ID 가져오기
        test_channel_id = os.getenv('TEST_CHANNEL_ID')
        role_id = os.getenv('RETROSPECTIVE_ROLE_ID')

        if not test_channel_id:
            # 테스트 채널이 없으면 일반 채널 사용
            test_channel_id = os.getenv('ATTENDANCE_CHANNEL_ID')

        if not test_channel_id or not role_id:
            await interaction.followup.send("❌ ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set in environment variables.", ephemeral=True)
            return

        # send_morning_check 함수 실행
        await send_morning_check(test_channel_id, role_id)
        await interaction.followup.send("✅ Morning check test completed! Check the test channel.", ephemeral=True)
        logger.info(f"{interaction.user} triggered test morning check")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to execute morning check: {e}", ephemeral=True)
        logger.error(f"Test morning check failed: {e}")


@bot.tree.command(name="test_evening_reminder", description="Test evening reminder")
async def test_evening_reminder_cmd(interaction: discord.Interaction):
    """저녁 리마인더를 테스트합니다."""
    await interaction.response.defer(ephemeral=True)

    try:
        # 테스트용 채널 ID와 역할 ID 가져오기
        test_channel_id = os.getenv('TEST_CHANNEL_ID')
        role_id = os.getenv('RETROSPECTIVE_ROLE_ID')

        if not test_channel_id:
            # 테스트 채널이 없으면 일반 채널 사용
            test_channel_id = os.getenv('ATTENDANCE_CHANNEL_ID')

        if not test_channel_id or not role_id:
            await interaction.followup.send("❌ ATTENDANCE_CHANNEL_ID or RETROSPECTIVE_ROLE_ID not set in environment variables.", ephemeral=True)
            return

        # send_evening_reminder 함수 실행
        await send_evening_reminder(test_channel_id, role_id)
        await interaction.followup.send("✅ Evening reminder test completed! Check the test channel.", ephemeral=True)
        logger.info(f"{interaction.user} triggered test evening reminder")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to execute evening reminder: {e}", ephemeral=True)
        logger.error(f"Test evening reminder failed: {e}")


if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('DISCORD_TOKEN environment variable is not set')
        raise ValueError('DISCORD_TOKEN environment variable is not set. Please check your .env file.')

    logger.info('Starting bot...')
    bot.run(token)
