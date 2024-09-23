from faststream.rabbit import RabbitExchange
from corelib.broker import get_broker_settings

_settings = get_broker_settings()

RPC_EXCHANGE = RabbitExchange(
    f'rpc.{_settings.RABBITMQ_DEFAULT_KEY_PREFIX}', auto_delete=True
)


__all__ = ['RPC_EXCHANGE']
