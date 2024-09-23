import functools
import os
import secrets
import socket
from typing import List, Optional, Union

import orjson
from pydantic import (
    field_validator,
    AnyHttpUrl,
    HttpUrl,
    ValidationInfo,
    AfterValidator,
    DirectoryPath,
)
from pydantic_settings import SettingsConfigDict
from typing_extensions import Annotated

from ..broker import RabbitMQSettings
from ..cache import RedisSettings
from ..cloud import CloudSettings
from ..constants import Environments
from ..storage import StorageSettings

_url_list_type = Annotated[
    Union[Optional[str], Optional[List[AnyHttpUrl]]],
    AfterValidator(lambda v: [str(url).rstrip('/') for url in v]),
]


class Settings(StorageSettings, RedisSettings, RabbitMQSettings, CloudSettings):
    ROOT_PATH: str = ''
    SECRET_KEY: str = secrets.token_urlsafe(32)

    PROJECT_NAME: str = 'PROJECT'
    SERVER_NAME: Optional[str] = None
    SERVER_URI: Optional[Annotated[AnyHttpUrl, AfterValidator(str)]] = None
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '['http://localhost', 'http://localhost:4200', 'http://localhost:3000', \
    # 'http://localhost:8080', 'http://local.dockertoolbox.tiangolo.com']'
    BACKEND_CORS_ORIGINS: _url_list_type = []

    @field_validator('SERVER_NAME', mode='before')
    @classmethod
    def assemble_server_name(cls, v: Optional[str], info: ValidationInfo) -> str:  # noqa
        name = socket.gethostbyaddr(socket.gethostname())[0]
        return f'{name}::{v or info.data.get("PROJECT_NAME")}'

    @field_validator('SERVER_URI', mode='before')
    @classmethod
    def assemble_server_host(cls, v: Union[str, List[str]]) -> Union[List[str], str]:  # noqa
        if isinstance(v, str):
            return v
        return 'http://{host}:{port}'.format(
            host=os.environ.get('UVICORN_HOST', 'localhost'), port=8080
        )

    AUTH_SERVICE_URL: Annotated[Optional[AnyHttpUrl], AfterValidator(str)] = None
    AUTH_SERVICE_VALIDATION_ENDPOINT: str = '/api/v1/token/validate'
    AUTH_TOKEN_CACHE_EXPIRE: int = 24 * 3600

    @field_validator('AUTH_SERVICE_URL', mode='before')
    @classmethod
    def assemble_auth_service_host(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:  # noqa
        if isinstance(v, str):
            return v
        return 'http://{host}:{port}'.format(
            host=os.environ.get('AUTH_SERVICE_HOST', 'localhost'),
            port=os.environ.get('AUTH_SERVICE_PORT', '8080'),
        )

    @classmethod
    def _assemble_comma_separated(
        cls, v: Union[Optional[str], Optional[List[AnyHttpUrl]]]
    ):
        if not v:
            return []
        if isinstance(v, str):
            if not v.startswith('['):
                return [i.strip() for i in v.split(',')]
            else:
                return orjson.loads(v)
        elif isinstance(v, (list, str)):
            return v

    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[Optional[str], Optional[List[str]]]
    ) -> Union[List[AnyHttpUrl]]:  # noqa
        return cls._assemble_comma_separated(v)

    SENTRY_DSN: Annotated[
        Optional[HttpUrl],
        AfterValidator(lambda v: None if str(v) == 'None' else str(v)),
    ] = None  # noqa

    @field_validator('SENTRY_DSN', mode='before')
    @classmethod
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:  # noqa
        if v and len(v) == 0:
            return None
        return v

    GOOGLE_MAPS_API_KEY: str = 'YOUR_KEY_HERE'

    API_KEY: str = 'YOUR_API_KEY_HERE'
    APP_ENV: Optional[Environments] = Environments.dev
    DEBUG: Optional[int] = None
    ACTIVATE_AUTHORIZATION: bool = False
    LOG_ERRORS_IN_FILES: bool = False
    FILE_LOG_BASE: Annotated[DirectoryPath, AfterValidator(str)] = '/var/log'

    @field_validator('APP_ENV', mode='before')
    @classmethod
    def assemble_env(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[Environments]:  # noqa
        if v is None:
            return v
        v = v.upper()
        try:
            return Environments(v)
        except ValueError:
            return Environments.prod

    @field_validator('DEBUG', mode='after')
    @classmethod
    def assemble_debug(cls, v: Optional[int], info: ValidationInfo) -> int:  # noqa
        if v is None:
            return info.data.get('APP_ENV', Environments.prod) == Environments.dev
        return v

    DRY_RUN: Optional[bool] = None  # For some of the unit tests

    model_config = SettingsConfigDict(case_sensitive=True)


@functools.cache
def get_settings() -> Settings:
    # populate cache
    from ..broker import get_broker_settings
    from ..cache import get_cache_settings
    from ..storage import get_storage_settings
    from ..cloud import get_cloud_settings

    get_broker_settings()
    get_cache_settings()
    get_storage_settings()
    get_cloud_settings()
    return Settings()
