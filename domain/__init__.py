from typing import Annotated

from pydantic import Field

from domain.events.union import Event
from domain.commands.union import Command

Message = Annotated[
    Event | Command,
    Field(discriminator='type'),
]
