from faststream.rabbit import RabbitRouter

from connectinno.infra.broker.exchanges import RPC_EXCHANGE
from connectinno.infra.broker.queues import RPC_PING

router = RabbitRouter()


@router.subscriber(RPC_PING, exchange=RPC_EXCHANGE)
async def ping() -> str:
    return 'pong'


__all__ = [
    'ping',
    'router',
]
