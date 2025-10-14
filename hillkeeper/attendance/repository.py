import logging
from datetime import datetime

from ..config import KST
from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')

TTL_7_DAYS = 604800  # 7 days


async def save_event(message_id: int, *, channel_id: int, role_id: int, ttl: int = TTL_7_DAYS):
    """
    출석 체크 이벤트를 저장합니다.
    메시지 정보와 함께 출석 이벤트를 Redis에 저장하고 TTL을 설정합니다.

    Args:
        message_id: 디스코드 메시지 ID
        channel_id: 채널 ID
        role_id: 멘션할 역할 ID
        ttl: 만료 시간(초) (기본값: 7일)
    """
    now = datetime.now(KST)
    date = now.date()

    key = f"attendance:event:{date}:{message_id}"
    await redis_client.client.hset(
        key,
        mapping={
            "message_id": str(message_id),
            "channel_id": str(channel_id),
            "role_id": str(role_id),
            "created_at": now.isoformat()
        }
    )
    await redis_client.client.expire(key, ttl)
    logger.info(f"Stored attendance event: {date}:{message_id} (ttl={ttl}s)")


async def save_response(message_id: int, user_id: int, *, username: str, response: str):
    """
    사용자 응답을 저장합니다.
    출석 체크 메시지에 대한 사용자의 이모지 반응을 Redis에 저장합니다.

    Args:
        message_id: 디스코드 메시지 ID
        user_id: 사용자 ID
        username: 사용자 표시 이름
        response: 응답 유형 ("yes" 또는 "no")
    """
    now = datetime.now(KST)

    key = f"attendance:response:{message_id}:{user_id}"
    await redis_client.client.hset(
        key,
        mapping={
            "user_id": str(user_id),
            "username": username,
            "response": response,  # "yes" or "no"
            "timestamp": now.isoformat()
        }
    )
    # 7일 후 자동 삭제
    await redis_client.client.expire(key, TTL_7_DAYS)
    logger.info(f"Stored user response: {user_id} -> {response} for message {message_id}")


async def get_today_messages() -> list[int]:
    """
    오늘 생성된 출석 체크 메시지 ID 목록을 반환합니다.

    Returns:
        오늘 날짜의 출석 메시지 ID 리스트
    """
    date = datetime.now(KST).date()
    pattern = f"attendance:event:{date}:*"

    message_ids = []
    async for key in redis_client.client.scan_iter(match=pattern):
        # "attendance:event:2024-01-15:123456" -> 123456
        message_id = int(key.split(":")[-1])
        message_ids.append(message_id)

    return message_ids


async def get_event(message_id: int, date: datetime.date = None) -> dict | None:
    """
    특정 이벤트 정보를 조회합니다.

    Args:
        message_id: 메시지 ID
        date: 조회할 날짜 (기본값: 오늘)

    Returns:
        이벤트 데이터 딕셔너리. 존재하지 않으면 None
    """
    if date is None:
        date = datetime.now(KST).date()

    key = f"attendance:event:{date}:{message_id}"
    data = await redis_client.client.hgetall(key)

    if not data:
        return None

    return data


async def get_responses(message_id: int) -> list[dict]:
    """
    특정 메시지에 대한 모든 응답을 조회합니다.

    Args:
        message_id: 메시지 ID

    Returns:
        사용자 응답 데이터 리스트
    """
    pattern = f"attendance:response:{message_id}:*"

    responses = []
    async for key in redis_client.client.scan_iter(match=pattern):
        data = await redis_client.client.hgetall(key)
        if data:
            responses.append(data)

    return responses


async def delete_event(message_id: int, date: datetime.date = None):
    """
    특정 이벤트를 삭제합니다.

    Args:
        message_id: 메시지 ID
        date: 조회할 날짜 (기본값: 오늘)
    """
    if date is None:
        date = datetime.now(KST).date()

    key = f"attendance:event:{date}:{message_id}"
    await redis_client.client.delete(key)
    logger.info(f"Deleted attendance event: {date}:{message_id}")


