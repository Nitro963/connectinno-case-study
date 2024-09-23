from inspect import getmembers

from faststream.rabbit import RabbitExchange, RabbitQueue
from pika.adapters.blocking_connection import BlockingChannel

from connectinno.infra.broker import exchanges, queues
from connectinno.infra.broker.bindings import BINDINGS_MAP


def init_blocking_connection(channel: BlockingChannel):
    for _, exchange in getmembers(
        exchanges, lambda obj: isinstance(obj, RabbitExchange)
    ):
        channel.exchange_declare(
            exchange.name,
            exchange_type=exchange.type.value,
            passive=exchange.passive,
            durable=exchange.durable,
            auto_delete=exchange.auto_delete,
        )

    for _, queue in getmembers(queues, lambda obj: isinstance(obj, RabbitQueue)):
        # Every queue is automatically bound to the default exchange
        # with a routing key which is the same as the queue name
        channel.queue_declare(
            queue.name,
            durable=queue.durable,
            exclusive=queue.exclusive,
            auto_delete=queue.auto_delete,
            passive=queue.passive,
            arguments=queue.arguments,
        )

    for queue, bindings in BINDINGS_MAP.items():
        for exchange in bindings:
            channel.queue_bind(
                queue.name,
                exchange=exchange.name,
                routing_key=queue.routing_key,
                arguments=queue.bind_arguments,
            )

    return channel
