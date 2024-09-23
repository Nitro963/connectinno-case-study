from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
)

from corelib import timezone
from .base import metadata

transformations_table = Table(
    'transformations',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('image_id', Integer, ForeignKey('images.id'), nullable=False),
    Column('type', String, nullable=False),
    Column('created_at', DateTime, nullable=False, default=timezone.now),
)

gray_scale_transformations_table = Table(
    'gray_scale_transformations',
    metadata,
    Column('id', Integer, ForeignKey('transformations.id'), primary_key=True),
)

rotate_transformations_table = Table(
    'rotate_transformations',
    metadata,
    Column('id', Integer, ForeignKey('transformations.id'), primary_key=True),
    Column('angle', Integer, nullable=False),
    CheckConstraint('angle >= 1', name='angle_gte_one'),
    CheckConstraint('angle <= 360', name='angle_lte_360'),
)

resize_transformations_table = Table(
    'resize_transformations',
    metadata,
    Column(
        'id',
        Integer,
        ForeignKey('transformations.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True,
    ),
    Column('width', Integer, nullable=False),
    Column('height', Integer, nullable=False),
    CheckConstraint('width >= 1', name='width_gte_one'),
    CheckConstraint('width <= 4096', name='width_lte_4096'),
    CheckConstraint('height >= 1', name='height_gte_one'),
    CheckConstraint('height <= 4096', name='height_lte_2160'),
)
