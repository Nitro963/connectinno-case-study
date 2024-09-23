from sqlalchemy import Table, Column, Integer, String, DateTime

from corelib import timezone
from .base import metadata


images_table = Table(
    'images',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('location', String, nullable=False),
    Column('transformation_count', Integer, nullable=False, default=0),
    Column('created_at', DateTime, nullable=False, default=timezone.now),
)
