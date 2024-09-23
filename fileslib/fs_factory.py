import abc
import functools
import pathlib
from os import PathLike
from typing import Optional, Literal, Annotated, Union, Callable, Any

from fsspec import AbstractFileSystem
from fsspec.implementations.cache_mapper import create_cache_mapper
from fsspec.implementations.cached import CachingFileSystem
from fsspec.implementations.local import LocalFileSystem
from gcsfs import GCSFileSystem

from pydantic import BaseModel, DirectoryPath, HttpUrl, Field, model_serializer
from pydantic_core.core_schema import SerializationInfo


class IFSConfigs(BaseModel, metaclass=abc.ABCMeta):
    pass


class S3FSConfigs(IFSConfigs):
    type: Literal['s3-fs-configs'] = 's3-fs-configs'
    anon: bool = False
    endpoint_url: Optional[HttpUrl] = None
    max_concurrency: int = 1
    asynchronous: bool = False
    client_kwargs: Optional[dict] = None


class FileCacheFsConfigs(BaseModel):
    type: Literal['cached-fs-configs'] = 'cached-fs-configs'
    cache_storage: DirectoryPath
    expiry_time: int = 3 * 24 * 60 * 60  # 3 days in seconds
    check_files: bool = True
    same_names: bool = False


class LocalDiskFSConfigs(IFSConfigs):
    type: Literal['local-disk-fs-configs'] = 'local-disk-fs-configs'

    @model_serializer(when_used='json')
    def serialize_model(self, info: SerializationInfo):
        if isinstance(info.context, dict):
            if info.context.get('to', None) == 'fsspec':
                return {}
        return {
            'type': str(self.type),
        }


class GCSFSConfigs(IFSConfigs):
    type: Literal['gcs-fs-configs'] = 'gcs-fs-configs'
    project_id: str
    block_size: Optional[int] = None
    timeout: Optional[int] = None
    endpoint_url: Optional[str] = None
    consistency: str = 'none'
    token: Any

    @model_serializer(when_used='json')
    def serialize_model(self, info: SerializationInfo):
        if isinstance(info.context, dict):
            if info.context.get('to', None) == 'fsspec':
                return {
                    'project_id': self.project_id,
                    'token': self.token,
                    'block_size': self.block_size,
                    'timeout': self.timeout,
                    'consistency': self.consistency,
                    'endpoint_url': self.endpoint_url,
                }
        return {
            'type': str(self.type),
            'project_id': self.project_id,
            'block_size': self.block_size,
            'timeout': self.timeout,
            'consistency': self.consistency,
            'endpoint_url': self.endpoint_url,
            'token': None if self.token not in ['anon'] else self.token,
        }


FSConfigs = Annotated[
    Union[
        S3FSConfigs,
        GCSFSConfigs,
        LocalDiskFSConfigs,
    ],
    Field(discriminator='type'),
]


class DefaultFSFactory:
    def __init__(self, configs: IFSConfigs, default_cache_configs: FileCacheFsConfigs):
        self._default_cache_storage = default_cache_configs
        self._configs = configs

    def create(self) -> AbstractFileSystem:
        return LocalFileSystem(
            **self._configs.model_dump(mode='json', context={'to': 'fsspec'})
        )

    def cached(self, fs: AbstractFileSystem) -> CachingFileSystem:
        assert not isinstance(fs, CachingFileSystem), f'Unexpected type({type(fs)})'
        return CachingFileSystem(
            fs=fs,
            cache_storage=str(self._default_cache_storage.cache_storage),
            expiry_time=self._default_cache_storage.expiry_time,
            check_files=self._default_cache_storage.check_files,
            same_names=self._default_cache_storage.same_names,
        )

    def create_cache_mapper(self) -> Callable[[str], PathLike]:
        mapper = create_cache_mapper(self._default_cache_storage.same_names)

        @functools.wraps(mapper)
        def mapper_decorator(same_names: str):
            basename = mapper(same_names)
            return pathlib.Path(self._default_cache_storage.cache_storage).joinpath(
                basename
            )

        return mapper_decorator


class GCSFSFactory(DefaultFSFactory):
    def __init__(
        self, configs: GCSFSConfigs, default_cache_configs: FileCacheFsConfigs
    ):
        assert isinstance(configs, GCSFSConfigs)
        super().__init__(configs, default_cache_configs)

    def create(self) -> GCSFileSystem:
        assert isinstance(self._configs, GCSFSConfigs)  # Just to make linter happy! :)
        return GCSFileSystem(
            project=self._configs.project_id,
            token=self._configs.token,
            endpoint_url=self._configs.endpoint_url,
            timeout=self._configs.timeout,
            consistency=self._configs.consistency,
            block_size=self._configs.block_size,
        )


__all__ = [
    'DefaultFSFactory',
    'IFSConfigs',
    'S3FSConfigs',
    'LocalDiskFSConfigs',
    'FileCacheFsConfigs',
    'FSConfigs',
    'GCSFSFactory',
    'GCSFSConfigs',
]
