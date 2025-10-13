"""출석 데이터 저장소 모듈"""
import logging

from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')


async def save_message(message_id: int, *, channel_id: int):
    """출석 체크 메시지를 저장합니다."""
    key = f"attendance:message:{message_id}"
    await redis_client.client.hset(
        key,
        mapping={
            "channel_id": str(channel_id),
            "timestamp": str(int(__import__('time').time()))
        }
    )
    # 24시간 후 자동 삭제
    await redis_client.client.expire(key, 86400)
    logger.info(f"Stored attendance message: {message_id}")


async def get_all_messages() -> list[int]:
    """저장된 출석 체크 메시지 ID 목록을 반환합니다."""
    pattern = "attendance:message:*"
    keys = []
    async for key in redis_client.client.scan_iter(match=pattern):
        # "attendance:message:123456" -> 123456
        message_id = int(key.split(":")[-1])
        keys.append(message_id)
    return keys


async def delete_message(message_id: int):
    """출석 체크 메시지를 삭제합니다."""
    key = f"attendance:message:{message_id}"
    await redis_client.client.delete(key)
    logger.info(f"Deleted attendance message: {message_id}")


async def clear_all_messages():
    """모든 출석 체크 메시지를 삭제합니다."""
    pattern = "attendance:message:*"
    deleted = 0
    async for key in redis_client.client.scan_iter(match=pattern):
        await redis_client.client.delete(key)
        deleted += 1
    logger.info(f"Cleared {deleted} attendance messages")
