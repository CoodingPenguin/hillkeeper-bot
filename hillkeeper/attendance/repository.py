"""Attendance data access layer (Redis)."""
import logging
from dataclasses import dataclass
from datetime import datetime

from ..config import KST
from ..database.redis import redis_client

logger = logging.getLogger('hillkeeper')

TTL_7_DAYS = 604800  # 7 days


@dataclass(frozen=True, slots=True)
class AttendanceEvent:
    """Immutable representation of an attendance check event."""
    message_id: int
    channel_id: int
    role_id: int
    created_at: str


@dataclass(frozen=True, slots=True)
class UserResponse:
    """Immutable representation of a user's attendance response."""
    user_id: int
    username: str
    response: str
    timestamp: str


def _event_key(date, message_id: int) -> str:
    """Build the Redis key for an attendance event."""
    return f"attendance:event:{date}:{message_id}"


def _response_key(message_id: int, user_id: int) -> str:
    """Build the Redis key for a user response."""
    return f"attendance:response:{message_id}:{user_id}"


def _parse_id_from_key(key: str) -> int:
    """Extract the trailing numeric ID from a Redis key."""
    return int(key.split(":")[-1])


async def save_event(message_id: int, *, channel_id: int, role_id: int, ttl: int = TTL_7_DAYS):
    """
    Persist an attendance check event to Redis.

    Args:
        message_id: Discord message ID.
        channel_id: Channel ID.
        role_id: Mentioned role ID.
        ttl: Expiry in seconds (default: 7 days).
    """
    now = datetime.now(KST)
    date = now.date()

    key = _event_key(date, message_id)
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
    Persist a user's emoji response to Redis.

    Args:
        message_id: Discord message ID.
        user_id: User ID.
        username: User display name.
        response: "yes" or "no".
    """
    now = datetime.now(KST)

    key = _response_key(message_id, user_id)
    await redis_client.client.hset(
        key,
        mapping={
            "user_id": str(user_id),
            "username": username,
            "response": response,
            "timestamp": now.isoformat()
        }
    )
    await redis_client.client.expire(key, TTL_7_DAYS)
    logger.info(f"Stored user response: {user_id} -> {response} for message {message_id}")


async def get_today_messages() -> list[int]:
    """Return message IDs for today's attendance events."""
    date = datetime.now(KST).date()
    pattern = f"attendance:event:{date}:*"

    message_ids = []
    async for key in redis_client.client.scan_iter(match=pattern):
        message_ids.append(_parse_id_from_key(key))

    return message_ids


async def get_event(message_id: int, date: datetime.date = None) -> AttendanceEvent | None:
    """
    Fetch an attendance event by message ID.

    Args:
        message_id: The message ID.
        date: Date to look up (defaults to today).

    Returns:
        An AttendanceEvent, or None if not found.
    """
    if date is None:
        date = datetime.now(KST).date()

    key = _event_key(date, message_id)
    data = await redis_client.client.hgetall(key)

    if not data:
        return None

    return AttendanceEvent(
        message_id=int(data["message_id"]),
        channel_id=int(data["channel_id"]),
        role_id=int(data["role_id"]),
        created_at=data["created_at"],
    )


async def get_responses(message_id: int) -> list[UserResponse]:
    """
    Fetch all user responses for a given message.

    Args:
        message_id: The message ID.

    Returns:
        A list of UserResponse objects.
    """
    pattern = f"attendance:response:{message_id}:*"

    responses = []
    async for key in redis_client.client.scan_iter(match=pattern):
        data = await redis_client.client.hgetall(key)
        if data:
            responses.append(UserResponse(
                user_id=int(data["user_id"]),
                username=data["username"],
                response=data["response"],
                timestamp=data["timestamp"],
            ))

    return responses


async def delete_event(message_id: int, date: datetime.date = None):
    """
    Delete an attendance event from Redis.

    Args:
        message_id: The message ID.
        date: Date to look up (defaults to today).
    """
    if date is None:
        date = datetime.now(KST).date()

    key = _event_key(date, message_id)
    await redis_client.client.delete(key)
    logger.info(f"Deleted attendance event: {date}:{message_id}")
