import os

from dishka import Provider, provide, Scope
from firebase_admin import App as FirebaseApp
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from corelib.storage import StorageSettings
from fileslib.fs_factory import (
    DefaultFSFactory,
    FileCacheFsConfigs,
    LocalDiskFSConfigs,
    GCSFSFactory,
    GCSFSConfigs,
)


class FactoryProvider(Provider):
    @provide(scope=Scope.APP)
    def get_default_fs_factory(self, settings: StorageSettings) -> DefaultFSFactory:
        cache_dir = f'{settings.HOME_ROOT}/filecache'
        os.makedirs(cache_dir, exist_ok=True, mode=0o775)
        return DefaultFSFactory(
            configs=LocalDiskFSConfigs(),
            default_cache_configs=FileCacheFsConfigs(
                cache_storage=cache_dir,
            ),
        )

    @provide(scope=Scope.APP)
    def get_gcsfs_factory(
        self, settings: StorageSettings, app: FirebaseApp
    ) -> GCSFSFactory:
        cache_dir = f'{settings.HOME_ROOT}/filecache'
        os.makedirs(cache_dir, exist_ok=True, mode=0o775)
        return GCSFSFactory(
            configs=GCSFSConfigs(
                project_id=app.project_id, token=app.credential.get_credential()
            ),
            default_cache_configs=FileCacheFsConfigs(
                cache_storage=cache_dir,
            ),
        )

    @provide(scope=Scope.APP)
    def get_session_maker(self, engine: Engine) -> sessionmaker:
        return sessionmaker(
            bind=engine,
        )


__all__ = [
    'FactoryProvider',
]
