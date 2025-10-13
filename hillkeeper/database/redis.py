"""redis client"""
import logging
import redis.asyncio as redis

from ..config import get_env

logger = logging.getLogger('hillkeeper')


class RedisClient:

    def __init__(self):
        self._client: redis.Redis | None = None

    async def connect(self):
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
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis disconnected")

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()
