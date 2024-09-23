import asyncio
import logging
from inspect import Parameter
from typing import Callable, Dict, List, Type

from dishka import Container, Scope, AsyncContainer
from dishka.integrations.base import wrap_injection

from corelib.patterns import Singleton
from domain import Message
from domain.commands.base import CommandBase
from domain.events.base import EventBase
from .unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class MessageBus(metaclass=Singleton):
    @property
    def is_async(self) -> bool:
        return False

    def __init__(
        self,
        event_handlers: Dict[Type[EventBase], List[Callable]],
        command_handlers: Dict[Type[CommandBase], Callable],
    ):
        self.event_handlers: Dict[Type[EventBase], List[Callable]] = dict()
        self.command_handlers: Dict[Type[CommandBase], Callable] = dict()
        for key in event_handlers.keys():
            self.event_handlers[key] = [
                wrap_injection(  # type: ignore
                    func=handler,
                    is_async=self.is_async,
                    container_getter=lambda _, kwargs: kwargs['container'],
                    additional_params=[
                        Parameter(
                            name='container',
                            annotation=Container,
                            kind=Parameter.KEYWORD_ONLY,
                        )
                    ],
                )
                for handler in event_handlers[key]
            ]

        for key in command_handlers.keys():
            self.command_handlers[key] = wrap_injection(  # type: ignore
                func=command_handlers[key],
                is_async=self.is_async,
                container_getter=lambda _, kwargs: kwargs['container'],
                additional_params=[
                    Parameter(
                        name='container',
                        annotation=Container,
                        kind=Parameter.KEYWORD_ONLY,
                    )
                ],
            )

    def handle(self, container: Container, message: Message):
        queue = [message]
        results = []
        while queue:
            message = queue.pop(0)
            if isinstance(message, EventBase):
                self.handle_event(container, message, queue)
            elif isinstance(message, CommandBase):
                results.append(self.handle_command(container, message, queue))
            else:
                raise Exception(f'{message} was not an Event or Command')
        return results

    def handle_event(self, container: Container, event: EventBase, queue):
        uow = container.get(AbstractUnitOfWork)
        found = False
        for handler in self.event_handlers.get(type(event), []):
            found = True
            try:
                logger.debug('handling event %s with handler %s', event, handler)
                with container(
                    {type(event): event}, scope=Scope.STEP
                ) as step_container:
                    handler(event, container=step_container)
                queue.extend(uow.collect_new_events())
            except Exception:  # noqa
                logger.exception('Exception handling event %s', event)
                continue
        if not found:
            logger.warning(f'Could not find a handler for {event}')
            queue.extend(uow.collect_new_events())

    def handle_command(self, container: Container, command: CommandBase, queue):
        uow = container.get(AbstractUnitOfWork)
        logger.debug('handling command %s', command)
        try:
            handler = self.command_handlers.get(type(command), None)
            if not handler:
                raise NotImplementedError(f'Could not find a handler for {command}')
            with container(
                {type(command): command}, scope=Scope.STEP
            ) as step_container:
                result = handler(command, container=step_container)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise


class AsyncMessageBus(MessageBus):
    @property
    def is_async(self) -> bool:
        return True

    def __init__(
        self,
        event_handlers: Dict[Type[EventBase], List[Callable]],
        command_handlers: Dict[Type[CommandBase], Callable],
    ):
        super().__init__(
            event_handlers=event_handlers, command_handlers=command_handlers
        )

    async def handle(self, container: AsyncContainer, message: Message):
        queue = [message]
        results = []
        while queue:
            message = queue.pop(0)
            if isinstance(message, EventBase):
                await self.handle_event(container, message, queue)
            elif isinstance(message, CommandBase):
                results.append(await self.handle_command(container, message, queue))
            else:
                raise Exception(f'{message} was not an Event or Command')
        return results

    async def handle_event(
        self,
        container: AsyncContainer,
        event: EventBase,
        queue,
    ):
        uow = await container.get(AbstractUnitOfWork)
        found = False
        for handler in self.event_handlers.get(type(event), []):
            found = True
            try:
                logger.debug('handling event %s with handler %s', event, handler)
                async with container(
                    {type(event): event}, scope=Scope.STEP
                ) as step_container:
                    result = handler(event, container=step_container)
                    if asyncio.iscoroutine(result):
                        await result
                queue.extend(uow.collect_new_events())
            except Exception:  # noqa
                logger.exception('Exception handling event %s', event)
                continue
        if not found:
            logger.warning(f'Could not find a handler for {event}')
            queue.extend(uow.collect_new_events())

    async def handle_command(
        self,
        container: AsyncContainer,
        command: CommandBase,
        queue,
    ):
        uow = await container.get(AbstractUnitOfWork)
        logger.debug('handling command %s', command)
        try:
            handler = self.command_handlers.get(type(command), None)
            if not handler:
                raise NotImplementedError(f'Could not find a handler for {command}')
            async with container(
                {type(command): command}, scope=Scope.STEP
            ) as step_container:
                result = handler(command, container=step_container)
                if asyncio.iscoroutine(result):
                    result = await result
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise
