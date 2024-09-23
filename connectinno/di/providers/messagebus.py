from dishka import Provider, provide, Scope

from connectinno.app.messagebus import MessageBus, AsyncMessageBus


class MessageBusProvider(Provider):
    @provide(scope=Scope.APP)
    def get_message_bus(self) -> MessageBus:
        return MessageBus(
            event_handlers={},
            command_handlers={},
        )

    @provide(scope=Scope.APP)
    def get_async_message_bus(self) -> AsyncMessageBus:
        # TODO import handlers
        return AsyncMessageBus(
            event_handlers={},
            command_handlers={},
        )
