from faststream.rabbit import RabbitBroker
from redis.asyncio import Redis as AsyncRedis

from corelib.patterns import Singleton


class StartupProxy(metaclass=Singleton):
    def __init__(self, broker: RabbitBroker, redis: AsyncRedis):
        self.broker = broker
        self.redis = redis

    async def authenticate(self, token: str):
        # TODO implement rpc call
        pass

    async def get_user_info(self, token: str):
        pass

    async def get_user_permissions(self, user_id: int, user_type: str):
        pass
