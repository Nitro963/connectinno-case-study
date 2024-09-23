from sqlalchemy import Table, Column, Integer, String
from .base import metadata

users_table = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('age', Integer, nullable=False),
)
