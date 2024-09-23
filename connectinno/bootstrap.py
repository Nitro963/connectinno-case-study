import warnings

from dishka import make_container, make_async_container, AsyncContainer
from connectinno.di.providers.factory import FactoryProvider
from connectinno.di.providers.messagebus import MessageBusProvider
from connectinno.di.providers.persistence import (
    PersistenceStorageProvider,
    AsyncPersistenceStorageProvider,
)
from connectinno.di.providers.proxy import ProxyProvider
from connectinno.di.providers.rabbitmq import (
    RabbitMQProvider,
    AsyncRabbitMQProvider,
)
from connectinno.di.providers.redis import RedisProvider, AsyncRedisProvider
from connectinno.di.providers.unit_of_work import UnitOfWorkProvider
from connectinno.di.providers.firebase import FireBaseConfigsProvider
from connectinno.infra.db.alchemy.map import start_mappers as start_alchemy


def bootstrap_sync(essential_only=True, di_sync=True):  # noqa
    warnings.filterwarnings('ignore')
    if di_sync:
        container = make_container(
            RedisProvider(),
            RabbitMQProvider(),
            PersistenceStorageProvider(),
            UnitOfWorkProvider(),
            MessageBusProvider(),
            FactoryProvider(),
            FireBaseConfigsProvider(),
        )
    else:
        container = make_async_container(
            AsyncRedisProvider(),
            AsyncRabbitMQProvider(),
            AsyncPersistenceStorageProvider(),
            UnitOfWorkProvider(),
            MessageBusProvider(),
            ProxyProvider(),
            FactoryProvider(),
            FireBaseConfigsProvider(),
        )
    return container


async def init_async_connections(start_mappers: bool = False):
    if start_mappers:
        start_alchemy()


async def bootstrap(container: AsyncContainer, start_mappers=False):  # noqa
    await init_async_connections(start_mappers)
    # await asyncio.gather(
    #     container.get(AsyncRedis),
    #     container.get(AsyncQdrantClient),
    #     container.get(AsyncMessageBus),
    # )


__all__ = ['bootstrap_sync', 'bootstrap']
