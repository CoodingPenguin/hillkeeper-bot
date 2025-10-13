"""redis client"""
import logging
import redis.asyncio as redis

from ..config import get_env

logger = logging.getLogger('hillkeeper')


class RedisClient:
    """
    Redis 클라이언트 관리 클래스.
    비동기 Redis 연결을 관리하고 싱글톤 패턴으로 클라이언트를 제공합니다.
    """

    def __init__(self):
        self._client: redis.Redis | None = None

    async def connect(self):
        """
        Redis 서버에 연결합니다.
        REDIS_URL 환경 변수를 사용하여 연결하고 ping으로 연결을 확인합니다.
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
        """
        Redis 연결을 종료합니다.
        """
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis disconnected")

    @property
    def client(self) -> redis.Redis:
        """
        Redis 클라이언트 인스턴스를 반환합니다.

        Returns:
            연결된 Redis 클라이언트

        Raises:
            RuntimeError: 연결되지 않은 상태에서 접근 시
        """
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()
