import abc
from typing import Generator, Any

from sqlalchemy.orm import Session

from domain import Message
from domain.commands.base import CommandBase
from domain.events.base import EventBase
from connectinno.ports.repository import IRepository
from connectinno.adapters.image_repository import ImageRepository
from connectinno.adapters.transformation_repository import TransformationRepository
from fileslib.fs_factory import GCSFSFactory
from fileslib.registry import Registry


class AbstractUnitOfWork(metaclass=abc.ABCMeta):
    images: Any
    transformations: Any
    file_registry: Registry

    def __enter__(self) -> 'AbstractUnitOfWork':
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self) -> Generator[CommandBase | EventBase, None, None]:
        for key, field in vars(self).items():
            if isinstance(field, IRepository):
                for obj in field.seen:
                    if isinstance(obj, dict):
                        events = obj.get('events', None)
                        obj['events'] = []
                    else:
                        events = getattr(obj, 'events', None)
                        if hasattr(obj, 'events'):
                            events = obj.events
                            obj.events = []
                    if events:
                        assert isinstance(events, list)
                        while events:
                            yield events.pop(0)
            if isinstance(field, set):
                field = list(field)
                setattr(self, key, set())
            if isinstance(field, dict):
                field = list(field.values())
                setattr(self, key, dict())
            if isinstance(field, list):
                while field:
                    obj = field.pop(0)
                    if isinstance(obj, CommandBase | EventBase):
                        yield obj
                        continue
                    events = []
                    if isinstance(obj, dict) and 'events' in obj.keys():
                        events = obj['events']
                        obj['events'] = []
                    if hasattr(obj, 'events'):
                        events = obj.events
                        obj.events = []
                    if events:
                        while events:
                            event = events.pop(0)
                            assert isinstance(event, CommandBase | EventBase)
                            yield event

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


class AlchemyUnitOfWork(AbstractUnitOfWork):
    messages: list[Message]

    def __init__(self, session: Session, factory: GCSFSFactory):
        super().__init__()
        self.messages = list()
        self.session = session
        fs = factory.create()
        self.file_registry = Registry(bind=fs)
        self.images = ImageRepository(session, fs)
        self.transformations = TransformationRepository(session)

    def rollback(self):
        self.file_registry.rollback()
        self.session.rollback()

    def _commit(self):
        self.file_registry.commit()
        self.session.commit()
