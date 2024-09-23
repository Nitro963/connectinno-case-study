import functools
import socket
import time
from datetime import timedelta
from typing import Optional

from celery import Celery
from pydantic import field_validator, ValidationInfo, computed_field
from pydantic_settings import SettingsConfigDict

from ..broker import RabbitMQSettings
from ..cache import RedisSettings
from ..constants import Environments
from ..storage import StorageSettings


class CelerySettings(StorageSettings, RabbitMQSettings, RedisSettings):
    PROJECT_NAME: str = '0-plus-AI'
    SERVER_NAME: Optional[str] = None
    DEBUG: Optional[int] = None
    APP_ENV: Optional[Environments] = Environments.dev

    CELERY_EXECUTION_EVENTS_EXCHANGE: str = 'celery.execution_events'

    @field_validator('SERVER_NAME', mode='before')
    @classmethod
    def assemble_server_name(cls, v: Optional[str], info: ValidationInfo) -> str:  # noqa
        name = socket.gethostbyaddr(socket.gethostname())[0]
        return f'{name}::{v or info.data.get("PROJECT_NAME")}'

    @field_validator('DEBUG', mode='before')
    @classmethod
    def assemble_debug(cls, v: Optional[int], info: ValidationInfo) -> int:  # noqa
        if v is None:
            return info.data.get('APP_ENV', Environments.dev) == Environments.dev
        return v

    @field_validator('APP_ENV', mode='before')
    @classmethod
    def assemble_env(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[Environments]:  # noqa
        if v is None:
            return v
        v = v.upper()
        return Environments(v)

    broker_connection_retry_on_startup: bool = True
    override_backends: dict = {'redis': 'corelib.celery.backends.RedisBackend'}
    result_extended: bool = True
    result_expires: timedelta = timedelta(days=3)
    result_serializer: str = 'json'

    task_track_started: bool = True
    task_acks_late: bool = False
    task_reject_on_worker_lost: bool = True
    task_default_queue: str = 'celery_default'
    task_routes: dict = {
        'corelib.tasks.hello_world': {
            'queue': 'celery_hello',
            'delivery_mode': 'transient',
        },
    }

    @computed_field
    @property
    def result_backend(self) -> str:
        return self.REDIS_URL

    @computed_field
    @property
    def broker_url(self) -> str:
        return self.RABBITMQ_URL

    def to_celery_config_dict(self):
        return self.model_dump(
            warnings=False,
            include={
                'broker_connection_retry_on_startup',
                'override_backends',
                'broker_url',
                'result_backend',
                'result_extended',
                'result_expires',
                'result_serializer',
                'task_track_started',
                'task_acks_late',
                'task_reject_on_worker_lost',
                'task_default_queue',
                'task_routes',
            },
        )

    model_config = SettingsConfigDict(case_sensitive=True)


@functools.cache
def get_celery_settings() -> CelerySettings:
    # populate cache
    from ..broker import get_broker_settings
    from ..cache import get_cache_settings
    from ..storage import get_storage_settings

    get_broker_settings()
    get_cache_settings()
    get_storage_settings()
    return CelerySettings()


@functools.cache
def get_celery_result_backend():
    from redis import Redis

    _settings = get_celery_settings()
    return Redis.from_url(
        _settings.result_backend, decode_responses=True, single_connection_client=True
    )


@functools.cache
def get_mq_connection():
    from pika import BlockingConnection, URLParameters
    from pika.exchange_type import ExchangeType

    settings = get_celery_settings()
    params = URLParameters(url=settings.broker_url)
    params.heartbeat = 600
    params.blocked_connection_timeout = 300
    conn = BlockingConnection(params)
    channel = conn.channel()
    channel.exchange_declare(
        settings.CELERY_EXECUTION_EVENTS_EXCHANGE, ExchangeType.topic
    )
    return channel


def build_application(name: Optional[str] = None, strict_typing=True) -> Celery:
    settings = get_celery_settings()
    _app = Celery(name or settings.SERVER_NAME, strict_typing=strict_typing)

    _app.config_from_object(settings.to_celery_config_dict())

    return _app


def build_event_message_properties(_settings: CelerySettings):
    from pika import BasicProperties, DeliveryMode

    return BasicProperties(
        content_type='application/json',
        content_encoding='utf-8',
        timestamp=int(time.time()),
        type='event',
        delivery_mode=DeliveryMode.Persistent,
        app_id=_settings.PROJECT_NAME,
    )
