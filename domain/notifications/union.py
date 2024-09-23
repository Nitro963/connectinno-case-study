from inspect import getmembers, isclass
from typing import Annotated

from pydantic import Field

from .base import NotificationBase

modules = []

Notification = NotificationBase

for module in modules:
    for _, subclass in getmembers(
        module, lambda t: isclass(t) and issubclass(t, NotificationBase)
    ):
        Notification |= subclass

TNotification = Annotated[Notification, Field(discriminator='type')]
__all__ = ['TNotification']
