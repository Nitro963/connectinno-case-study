import pymongo
from beanie import Document
from pymongo import IndexModel

from .base import BaseModel


class Message(Document, BaseModel):
    # TODO complete model implementation, inherit from domain

    class Settings:
        name = 'messages'
        indexes = [
            IndexModel([('created_at', pymongo.DESCENDING)]),
        ]


__all__ = ['Message']
