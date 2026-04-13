"""Configuration and constants."""
import datetime
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Timezone
KST = ZoneInfo("Asia/Seoul")

# Day of week
THURSDAY = 3
DAY_NAMES: dict[str, int] = {
    "월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3,
    "금요일": 4, "토요일": 5, "일요일": 6,
}
DAY_NAMES_REVERSE: dict[int, str] = {v: k for k, v in DAY_NAMES.items()}

# Default meeting schedule
DEFAULT_MEETING_WEEKDAY = THURSDAY
DEFAULT_MEETING_HOUR = 22
DEFAULT_MEETING_MINUTE = 0
REMINDER_LEAD_MINUTES = 15

# Emoji
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_MIC = "🎤"

# Colors
COLOR_BLUE = 0x58ABFF
COLOR_YELLOW = 0xF1C40F
COLOR_DARK_BLUE = 0x34A5DB
COLOR_GREEN = 0x2ECC71


def calculate_reminder_time(*, hour: int, minute: int) -> datetime.time:
    """Calculate the reminder time (REMINDER_LEAD_MINUTES before meeting)."""
    meeting = datetime.datetime(2000, 1, 1, hour, minute)
    reminder = meeting - datetime.timedelta(minutes=REMINDER_LEAD_MINUTES)
    return datetime.time(hour=reminder.hour, minute=reminder.minute, tzinfo=KST)


def get_env(key: str, *, default: str = None, required: bool = False) -> str:
    """
    Retrieve an environment variable.

    Args:
        key: Environment variable name.
        default: Fallback value if not set.
        required: If True, raise when the variable is missing.

    Returns:
        The environment variable value.

    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"{key} environment variable is required")
    return value
