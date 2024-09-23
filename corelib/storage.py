import functools
from typing import Annotated, Optional

from pydantic import (
    AfterValidator,
    DirectoryPath,
    AnyUrl,
    field_validator,
    ValidationInfo,
    Field,
)
from pydantic_settings import BaseSettings


class StorageSettings(BaseSettings):
    HOME_ROOT: Annotated[DirectoryPath, AfterValidator(str)] = '/home'
    MEDIA_ROOT: Annotated[DirectoryPath, AfterValidator(str)] = '/home/media'

    LOW_MEM: bool = True

    # Assuming mongodb by default
    SQL_DB_HOST: str = 'localhost'
    SQL_DB_PORT: str = '27017'
    SQL_DB_USERNAME: str = 'user'
    SQL_DB_PASSWORD: str = 'password'
    SQL_DB_NAME: str = 'default_db'
    SQL_DB_DRIVER: str = 'mysql'
    SQL_DB_URL: Annotated[Optional[AnyUrl], AfterValidator(str)] = Field(
        None, exclude=True
    )

    @field_validator('SQL_DB_URL', mode='before')
    @classmethod
    def assemble_sqldb_connection(cls, v: Optional[str], info: ValidationInfo) -> str:  # noqa
        if isinstance(v, str):
            return v
        return '{driver}://{username}:{password}@{host}:{port}/{name}'.format(
            driver=info.data.get('SQL_DB_DRIVER'),
            username=info.data.get('SQL_DB_USERNAME'),
            password=info.data.get('SQL_DB_PASSWORD'),
            host=info.data.get('SQL_DB_HOST'),
            port=info.data.get('SQL_DB_PORT'),
            name=info.data.get('SQL_DB_NAME'),
        )

    # Assuming mongodb by default
    NOSQL_DB_HOST: str = 'localhost'
    NOSQL_DB_PORT: str = '27017'
    NOSQL_DB_USERNAME: str = 'user'
    NOSQL_DB_PASSWORD: str = 'password'
    NOSQL_DB_NAME: str = 'default_db'
    NOSQL_DB_DRIVER: str = 'mongodb'
    NOSQL_AUTH_DATABASE: str = 'default_db'
    NOSQL_DB_URL: Annotated[Optional[AnyUrl], AfterValidator(str)] = Field(
        None, exclude=True
    )

    @field_validator('NOSQL_DB_URL', mode='before')
    @classmethod
    def assemble_nosqldb_connection(cls, v: Optional[str], info: ValidationInfo) -> str:  # noqa
        if isinstance(v, str):
            return v
        return '{driver}://{username}:{password}@{host}:{port}/{name}?authSource={auth_db}'.format(
            driver=info.data.get('NOSQL_DB_DRIVER'),
            username=info.data.get('NOSQL_DB_USERNAME'),
            password=info.data.get('NOSQL_DB_PASSWORD'),
            host=info.data.get('NOSQL_DB_HOST'),
            port=info.data.get('NOSQL_DB_PORT'),
            name=info.data.get('NOSQL_DB_NAME'),
            auth_db=info.data.get('NOSQL_AUTH_DATABASE'),
        )

    QDRANT_DB_HOST: str = 'localhost'
    QDRANT_DB_PORT: str = '6333'
    QDRANT_DB_API_KEY: Optional[str] = None
    QDRANT_DB_URL: Annotated[Optional[AnyUrl], AfterValidator(str)] = Field(
        None, exclude=True
    )

    @field_validator('QDRANT_DB_URL', mode='before')
    @classmethod
    def assemble_qdrant_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:  # noqa
        if isinstance(v, str):
            return v
        return 'http://{host}:{port}'.format(
            host=info.data.get('QDRANT_DB_HOST'),
            port=info.data.get('QDRANT_DB_PORT'),
        )


@functools.cache
def get_storage_settings() -> StorageSettings:
    return StorageSettings()
