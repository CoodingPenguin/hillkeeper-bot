"""설정 및 상수 관리"""
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 타임존 설정
KST = ZoneInfo("Asia/Seoul")

# 요일 상수
THURSDAY = 3

# 이모지 상수
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_MIC = "🎤"


def get_env(key: str, *, default: str = None, required: bool = False) -> str:
    """
    환경 변수를 가져옵니다.

    Args:
        key: 환경 변수 키
        default: 기본값 (없을 경우 None)
        required: 필수 여부. True이면 값이 없을 때 예외 발생

    Returns:
        환경 변수 값

    Raises:
        ValueError: required=True인데 값이 없을 경우
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"{key} environment variable is required")
    return value
