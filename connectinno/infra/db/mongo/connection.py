from inspect import getmembers, isclass

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def start_mappers(client: AsyncIOMotorClient):
    from . import models
    from beanie import Document

    beanie_models = [
        '.'.join([doc[1].__module__, doc[1].__name__])
        for doc in getmembers(models)
        if isclass(doc[1]) and issubclass(doc[1], Document) and doc[1] != Document
    ]
    await init_beanie(
        database=client.get_default_database(), document_models=beanie_models
    )
