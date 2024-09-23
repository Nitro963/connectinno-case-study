from faststream.rabbit import RabbitQueue


RPC_PING = RabbitQueue('ping', auto_delete=True)

__all__ = [
    'RPC_PING',
]
