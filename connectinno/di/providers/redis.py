from typing import Iterable, Optional, AsyncIterable

from dishka import Provider, provide, Scope, alias
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from corelib.cache import RedisSettings
from connectinno.di.keys import KeysGenerator


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    def get_keygen(self) -> KeysGenerator:
        return KeysGenerator()

    @provide(scope=Scope.APP)
    def get_redis_settings(self) -> RedisSettings:
        return RedisSettings()

    @provide(scope=Scope.APP)
    def get_redis_client(self, settings: RedisSettings) -> Iterable[Redis]:
        client = Redis.from_url(
            url=settings.REDIS_URL, decode_responses=True, single_connection_client=True
        )
        yield client
        client.close()

    @provide(scope=Scope.APP)
    def get_async_redis_client(self) -> Optional[AsyncRedis]:
        return None


class AsyncRedisProvider(RedisProvider):
    _optional_async_redis = alias(source=AsyncRedis, provides=Optional[AsyncRedis])

    @provide(scope=Scope.APP)
    async def get_async_redis_client(
        self, settings: RedisSettings
    ) -> AsyncIterable[AsyncRedis]:
        client = AsyncRedis.from_url(
            url=settings.REDIS_URL, decode_responses=True, single_connection_client=True
        )
        await client.initialize()
        yield client
        await client.close()
