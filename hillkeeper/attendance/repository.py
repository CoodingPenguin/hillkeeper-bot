import logging
from datetime import datetime

from ..config import KST
from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')

TTL_7_DAYS = 604800  # 7 days


async def save_event(message_id: int, *, channel_id: int, role_id: int):
    """출석 체크 이벤트를 저장합니다."""
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
    # 7일 후 자동 삭제
    await redis_client.client.expire(key, TTL_7_DAYS)
    logger.info(f"Stored attendance event: {date}:{message_id}")


async def save_response(message_id: int, user_id: int, *, username: str, response: str):
    """사용자 응답을 저장합니다."""
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
    """오늘 생성된 출석 체크 메시지 ID 목록을 반환합니다."""
    date = datetime.now(KST).date()
    pattern = f"attendance:event:{date}:*"

    message_ids = []
    async for key in redis_client.client.scan_iter(match=pattern):
        # "attendance:event:2024-01-15:123456" -> 123456
        message_id = int(key.split(":")[-1])
        message_ids.append(message_id)

    return message_ids


async def get_event(message_id: int, date: datetime.date = None) -> dict | None:
    """특정 이벤트 정보를 조회합니다."""
    if date is None:
        date = datetime.now(KST).date()

    key = f"attendance:event:{date}:{message_id}"
    data = await redis_client.client.hgetall(key)

    if not data:
        return None

    return data


async def get_responses(message_id: int) -> list[dict]:
    """특정 메시지에 대한 모든 응답을 조회합니다."""
    pattern = f"attendance:response:{message_id}:*"

    responses = []
    async for key in redis_client.client.scan_iter(match=pattern):
        data = await redis_client.client.hgetall(key)
        if data:
            responses.append(data)

    return responses


async def delete_event(message_id: int, date: datetime.date = None):
    """특정 이벤트를 삭제합니다."""
    if date is None:
        date = datetime.now(KST).date()

    key = f"attendance:event:{date}:{message_id}"
    await redis_client.client.delete(key)
    logger.info(f"Deleted attendance event: {date}:{message_id}")


async def clear_today_events():
    """오늘의 모든 이벤트를 삭제합니다."""
    date = datetime.now(KST).date()
    pattern = f"attendance:event:{date}:*"

    deleted = 0
    async for key in redis_client.client.scan_iter(match=pattern):
        await redis_client.client.delete(key)
        deleted += 1

    logger.info(f"Cleared {deleted} attendance events for {date}")
