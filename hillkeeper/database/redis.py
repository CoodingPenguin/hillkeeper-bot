"""Async Redis client wrapper."""
import logging
import redis.asyncio as redis

from ..config import get_env

logger = logging.getLogger('hillkeeper')


class RedisClient:
    """
    Manage an async Redis connection as a singleton.
    """

    def __init__(self):
        self._client: redis.Redis | None = None

    async def connect(self):
        """
        Connect to Redis using the REDIS_URL environment variable.
        Verifies the connection with a ping.
        """
        if self._client:
            logger.warning("Redis client already connected")
            return

        redis_url = get_env('REDIS_URL', required=True)

        self._client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        try:
            await self._client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis disconnected")

    @property
    def client(self) -> redis.Redis:
        """
        Return the connected Redis client.

        Raises:
            RuntimeError: If the client has not been connected yet.
        """
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()
