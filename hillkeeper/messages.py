"""메시지 템플릿 모듈"""
from .config import EMOJI_CHECK, EMOJI_CROSS, EMOJI_MIC

# 아침 출석 체크 메시지
MESSAGE_MORNING_CHECK = (
    "<@&{role_id}> 안녕하세요! 오늘 저녁 10시 회고 모임 참여 여부를 체크해주세요.\n\n"
    f"{EMOJI_CHECK} 참여\n"
    f"{EMOJI_CROSS} 불참"
)

# 저녁 리마인더 메시지
MESSAGE_EVENING_REMINDER = f"{{mentions}} 10시 회고 모임이 곧 시작됩니다. 음성 채널로 들어와 주세요! {EMOJI_MIC}"

# 참여자 없음 메시지
MESSAGE_NO_PARTICIPANTS = "아무도 참여 체크를 하지 않으셨네요. 😢"
