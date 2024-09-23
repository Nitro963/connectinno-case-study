from typing import AsyncIterable, Optional, Iterable

from dishka import Provider, provide, Scope, alias
from faststream.rabbit import RabbitBroker
from kombu import Connection, Producer, pools
from kombu.connection import ConnectionPool
from pika import BlockingConnection, URLParameters
from corelib.broker import RabbitMQSettings
from connectinno.infra.broker.connection import init_blocking_connection


class RabbitMQProvider(Provider):
    @provide(scope=Scope.APP)
    def get_rabbitmq_settings(self) -> RabbitMQSettings:
        return RabbitMQSettings()

    @provide(scope=Scope.APP)
    def get_blocking_connection_pool(
        self, settings: RabbitMQSettings
    ) -> Iterable[ConnectionPool]:
        conn = BlockingConnection(URLParameters(url=settings.RABBITMQ_URL))
        init_blocking_connection(conn.channel())
        conn.close()
        pool: ConnectionPool = pools.connections[Connection(settings.RABBITMQ_URL)]
        yield pool
        pool.force_close_all()

    @provide(scope=Scope.REQUEST)
    def get_rabbitmq_client(
        self,
        pool: ConnectionPool,
    ) -> Iterable[Producer]:
        client = pools.producers[pool.connection].acquire(block=True)
        yield client
        client.release()

    @provide(scope=Scope.APP)
    def get_async_rabbitmq_client(self, _: RabbitMQSettings) -> Optional[RabbitBroker]:
        return None


class AsyncRabbitMQProvider(RabbitMQProvider):
    _optional_async_client = alias(source=RabbitBroker, provides=Optional[RabbitBroker])

    @provide(scope=Scope.APP)
    async def get_async_rabbitmq_client(
        self, settings: RabbitMQSettings
    ) -> AsyncIterable[RabbitBroker]:
        broker = RabbitBroker(url=settings.RABBITMQ_URL)
        await broker.connect()
        yield broker
        await broker.close()
