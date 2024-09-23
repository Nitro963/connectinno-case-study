from inspect import getmembers, isclass
from typing import Annotated

from pydantic import Field

from .base import EventBase

modules = []

Event = EventBase

for module in modules:
    for _, subclass in getmembers(
        module, lambda t: isclass(t) and issubclass(t, EventBase)
    ):
        Event |= subclass

TEvent = Annotated[Event, Field(discriminator='type')]

__all__ = ['Event', 'TEvent']
