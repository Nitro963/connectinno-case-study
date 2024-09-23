from inspect import getmembers, isclass
from typing import Annotated

from pydantic import Field

from .base import CommandBase

modules = []

Command = CommandBase

for module in modules:
    for _, subclass in getmembers(
        module, lambda t: isclass(t) and issubclass(t, CommandBase)
    ):
        Command |= subclass

TCommand = Annotated[Command, Field(discriminator='type')]

__all__ = ['Command', 'TCommand']
