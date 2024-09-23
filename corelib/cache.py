import functools
from typing import Optional


from pydantic import RedisDsn, AfterValidator, field_validator, Field
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings
from typing_extensions import Annotated


class RedisSettings(BaseSettings):
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: str = '6379'
    REDIS_PASSWORD: str = 'password'
    REDIS_DB_NUMBER: str = '0'
    REDIS_URL: Annotated[Optional[RedisDsn], AfterValidator(str)] = Field(
        None, exclude=True
    )
    REDIS_DEFAULT_KEY_PREFIX: str = '0plus-ai'

    @field_validator('REDIS_URL', mode='before')
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        return 'redis://:{password}@{host}:{port}/{db}'.format(
            password=info.data.get('REDIS_PASSWORD'),
            host=info.data.get('REDIS_HOST'),
            port=info.data.get('REDIS_PORT'),
            db=info.data.get('REDIS_DB_NUMBER'),
        )


@functools.cache
def get_cache_settings() -> RedisSettings:
    return RedisSettings()
