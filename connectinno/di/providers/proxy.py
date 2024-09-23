from dishka import Provider, provide, Scope
from redis.asyncio import Redis as AsyncRedis
from faststream.rabbit import RabbitBroker

from connectinno.proxy import StartupProxy


class ProxyProvider(Provider):
    @provide(scope=Scope.APP)
    def get_proxy(self, broker: RabbitBroker, client: AsyncRedis) -> StartupProxy:
        return StartupProxy(broker, client)


__all__ = ['ProxyProvider']
