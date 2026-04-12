"""Configuration and constants."""
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Timezone
KST = ZoneInfo("Asia/Seoul")

# Day of week
THURSDAY = 3

# Emoji
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_MIC = "🎤"

# Colors
COLOR_BLUE = 0x58ABFF
COLOR_YELLOW = 0xF1C40F
COLOR_DARK_BLUE = 0x34A5DB


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
