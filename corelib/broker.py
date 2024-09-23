import asyncio
import enum
import functools
import time
from collections import defaultdict
from typing import Callable, Optional, Annotated

import orjson
from aio_pika import (
    connect_robust,
    ExchangeType,
    Message,
    DeliveryMode,
    IncomingMessage,
)
from aio_pika.abc import AbstractQueue, ConsumerTag, AbstractChannel, AbstractConnection
from aio_pika.patterns.rpc import JsonRPC, RPC
from pydantic import AmqpDsn, AfterValidator, field_validator, Field
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings


class RPCMode(int, enum.Enum):
    callee = 1
    caller = 2


class RabbitMQSettings(BaseSettings):
    RABBITMQ_HOST: str = 'localhost'
    RABBITMQ_PORT: str = '6379'
    RABBITMQ_VHOST: str = '/'
    RABBITMQ_USERNAME: str = 'guest'
    RABBITMQ_PASSWORD: str = 'guest'
    RABBITMQ_URL: Annotated[Optional[AmqpDsn], AfterValidator(str)] = Field(
        None, exclude=True
    )
    RABBITMQ_DEFAULT_KEY_PREFIX: str = '0plus-ai'

    @field_validator('RABBITMQ_URL', mode='before')
    @classmethod
    def assemble_amqp_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        return 'amqp://{username}:{password}@{host}:{port}/{vhost}'.format(
            username=info.data.get('RABBITMQ_USERNAME'),
            password=info.data.get('RABBITMQ_PASSWORD'),
            host=info.data.get('RABBITMQ_HOST'),
            port=info.data.get('RABBITMQ_PORT'),
            vhost=info.data.get('RABBITMQ_VHOST'),
        )


async def _on_message(message: IncomingMessage, f: Callable, raw: bool = False):
    if not raw:
        async with message.process():
            data = orjson.loads(message.body)
            if asyncio.iscoroutinefunction(f):
                res = await f(**data)
            else:
                res = f(**data)
            return res
    else:
        if asyncio.iscoroutinefunction(f):
            res = await f(message)
        else:
            res = f(message)
        return res


class Client:
    _connection_not_initialized_message = 'Connection is not initialized yet!'

    def __init__(self, url, name):
        self._connection: Optional[AbstractConnection] = None
        self._url = url
        self._rpc: Optional[RPC] = None
        self.name = name
        self._mode: Optional[RPCMode] = None
        self._exchanges = dict()
        self._channel: Optional[AbstractChannel] = None
        self._events_queues = defaultdict(dict)

    async def init_connection(self, rpc_mode=RPCMode.callee, loop=None):
        if self._connection:
            return
        self._connection = await connect_robust(self._url, loop=loop)
        self._channel = await self._connection.channel()
        if rpc_mode is not None:
            self._rpc = await JsonRPC.create(self._channel, exchange=f'rpc.{self.name}')
        self._mode = rpc_mode
        return self._connection

    async def register_procedure(self, task: Callable):
        return await self._rpc.register(task.__name__, task, auto_delete=True)

    async def create_event(
        self, exchange_name: str, exchange_type: ExchangeType = ExchangeType.FANOUT
    ):
        self._exchanges[exchange_name] = await self._channel.declare_exchange(
            exchange_name, exchange_type
        )

    async def subscribe_to_event(
        self,
        on_event: Callable,
        exchange_name: str,
        routing_key: str = '',
        raw: bool = False,
        exclusive: bool = False,
    ):
        if exchange_name not in self._exchanges.keys():
            await self.create_event(exchange_name)
        qu: AbstractQueue = await self._channel.declare_queue(
            exclusive=exclusive, durable=True, name=on_event.__name__
        )
        await qu.bind(self._exchanges[exchange_name], routing_key=routing_key)
        tag = await qu.consume(functools.partial(_on_message, f=on_event, raw=raw))
        self._events_queues[exchange_name][on_event.__name__] = qu, tag

    async def unsubscribe_from_event(self, on_event: Callable, event_name: str):
        subscriber: Optional[tuple[AbstractQueue, ConsumerTag]] = self._events_queues[
            event_name
        ].get(on_event.__name__, None)
        if not subscriber:
            raise ValueError('Subscriber not found.')
        qu, tag = subscriber
        await qu.cancel(tag)
        await qu.delete(if_unused=True, if_empty=True)

    async def close_connection(self):
        if self._rpc:
            await self._rpc.close()
        await self._connection.close()

    async def publish_event(
        self,
        exchange_name: str,
        data: dict | str,
        routing_key: str = 'info',
        event_type: str | None = 'event',
    ):
        assert isinstance(data, dict) or isinstance(data, str)
        message = Message(
            orjson.dumps(data) if isinstance(data, dict) else data.encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type='application/json',
            content_encoding='utf-8',
            type=event_type,
            app_id=self.name,
            timestamp=time.time(),
        )
        await self._exchanges[exchange_name].publish(message, routing_key=routing_key)
        # We need to supply a routing_key when sending, but its value is ignored for fanout exchanges

    @property
    def connection(self):
        if self._connection:
            return self._connection
        raise ConnectionError(self._connection_not_initialized_message)

    @property
    def rpc(self):
        if self._rpc:
            return self._rpc
        if self._mode is not None and not self.is_initialized:
            raise ConnectionError(self._connection_not_initialized_message)

        return None

    @property
    def is_initialized(self):
        return self.connection is not None


@functools.cache
def get_broker_settings() -> RabbitMQSettings:
    return RabbitMQSettings()


__all__ = ['Client', 'RPCMode', 'RabbitMQSettings', 'get_broker_settings']
