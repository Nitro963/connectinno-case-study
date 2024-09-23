from . import exchanges
from . import queues

BINDINGS_MAP = {
    queues.RPC_PING: [exchanges.RPC_EXCHANGE],
}
