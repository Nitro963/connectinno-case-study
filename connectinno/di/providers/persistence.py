from typing import AsyncIterable, Iterable, Optional

from dishka import Provider, Scope, provide, alias
from fsspec import AbstractFileSystem
from gcsfs import GCSFileSystem
from google.cloud import storage
from qdrant_client import QdrantClient, AsyncQdrantClient
from sqlalchemy import create_engine, Engine
from firebase_admin import App as FirebaseApp

from corelib.storage import StorageSettings
from fileslib.fs_factory import DefaultFSFactory, GCSFSFactory
from fileslib.storage_service_proxy import StorageServiceProxy


class PersistenceStorageProvider(Provider):
    @provide(scope=Scope.APP)
    def get_storage_settings(self) -> StorageSettings:
        return StorageSettings()

    @provide(scope=Scope.APP)
    def get_qdrant_client(self, settings: StorageSettings) -> Iterable[QdrantClient]:
        client = QdrantClient(
            url=settings.QDRANT_DB_URL, api_key=settings.QDRANT_DB_API_KEY
        )
        yield client
        client.close()

    @provide(scope=Scope.APP)
    def get_async_qdrant_client(
        self, settings: StorageSettings
    ) -> Optional[AsyncQdrantClient]:
        return None

    @provide(scope=Scope.APP)
    def get_default_fs(self, factory: DefaultFSFactory) -> AbstractFileSystem:
        return factory.create()

    @provide(scope=Scope.APP)
    def get_gcsfs(self, factory: GCSFSFactory) -> GCSFileSystem:
        return factory.create()

    @provide(scope=Scope.APP)
    def get_alchemy_engine(self, settings: StorageSettings) -> Engine:
        engine = create_engine(
            str(settings.SQL_DB_URL),
            echo=False,
        )
        # metadata.create_all(engine) # delegate to alembic
        return engine

    @provide(scope=Scope.APP)
    def get_storage_service_proxy(self, app: FirebaseApp) -> StorageServiceProxy:
        return StorageServiceProxy(
            bucket=f'{app.project_id}.appspot.com',
            client=storage.Client(
                project=app.project_id,
                credentials=app.credential.get_credential(),
            ),
        )


class AsyncPersistenceStorageProvider(PersistenceStorageProvider):
    _optional_async_qdrant_client = alias(
        source=AsyncQdrantClient, provides=Optional[AsyncQdrantClient]
    )

    @provide(scope=Scope.APP)
    async def get_async_qdrant_client(
        self, settings: StorageSettings
    ) -> AsyncIterable[AsyncQdrantClient]:
        client = AsyncQdrantClient(
            url=settings.QDRANT_DB_URL, api_key=settings.QDRANT_DB_API_KEY
        )
        yield client
        await client.close()
