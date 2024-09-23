import functools

from qdrant_client import QdrantClient, AsyncQdrantClient


@functools.cache
def get_client(url: str, api_key: str):
    return QdrantClient(url=url, api_key=api_key)


@functools.cache
def get_async_client(url: str, api_key: str):
    return AsyncQdrantClient(url=url, api_key=api_key)
