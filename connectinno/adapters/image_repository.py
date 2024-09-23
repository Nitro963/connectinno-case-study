from typing import Optional

from PIL import Image
from fsspec import AbstractFileSystem
from pydantic import TypeAdapter
from sqlalchemy import select, update

from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql.functions import rank, count, max as max_fn

from connectinno.infra.db.alchemy.models.image import images_table
from connectinno.infra.db.alchemy.models.transformation import (
    transformations_table,
)
from connectinno.ports.repository import ObjectDoesNotExists, IRepository
from domain.entities import ImageModel
from domain.aggregates.image import ImageAggregate
from domain.entities.image import TransformedImage


class ImageRepository(IRepository):
    def __init__(self, session: Session, fs: AbstractFileSystem):
        self.session = session
        self.seen = set()
        self.fs = fs

    def get(self, ref: int) -> ImageAggregate:
        result = self.session.execute(
            select(ImageModel).where(images_table.c.id == ref)
        )
        result = result.scalars().all()
        if not result:
            raise ObjectDoesNotExists()
        obj = result[0]
        aggregate = ImageAggregate(
            image_info=obj,
            fs=self.fs,
        )
        self.seen.add(aggregate)
        return aggregate

    def add(self, image_info: ImageModel, image: Image) -> ImageAggregate:
        assert image_info.location, 'location must exists'
        assert self.fs.exists(image_info.location), 'location must exists in fs'
        self.session.add(image_info)
        aggregate = ImageAggregate(
            image_info=image_info,
            fs=self.fs,
            image=image,
        )
        self.seen.add(aggregate)
        return aggregate

    def rank_images(self):
        rk = (
            rank()
            .over(order_by=images_table.c.transformation_count.desc())
            .label('rank')
        )
        stmt = select(images_table.c.id, images_table.c.name, rk).order_by(rk.asc())
        tuples = self.session.execute(stmt).all()
        return [
            dict(zip(['id', 'original_filename', 'rank'], values)) for values in tuples
        ]

    def sync_images_transformations(self, refs: Optional[list[int]] = None):
        stmt = select(
            transformations_table.c.image_id,
            count(transformations_table.c.id).label('count'),
        )

        if refs:
            stmt = stmt.where(transformations_table.c.image_id.in_(refs))

        subquery = stmt.group_by(transformations_table.c.image_id).alias('count')

        update_stmt = (
            update(images_table)
            .values(transformation_count=subquery.c.count)
            .where(images_table.c.id == subquery.c.image_id)  # noqa
        )
        self.session.execute(update_stmt)

    def update(self, aggregate: ImageAggregate):
        assert aggregate.image_info.location, 'location must exists'
        assert self.fs.exists(
            aggregate.image_info.location
        ), 'location must exists in fs'
        self.session.merge(aggregate.image_info)
        aggregate.image = None
        self.seen.add(aggregate)
        return aggregate

    def get_latest_transformations(self) -> list[TransformedImage]:
        subq = (
            select(
                transformations_table.c.image_id,
                max_fn(transformations_table.c.created_at).label('max_created_at'),
            )
            .group_by(transformations_table.c.image_id)
            .subquery()
        )

        latest_transformation = aliased(transformations_table)

        query = (
            select(
                images_table.c.id,
                images_table.c.name.label('original_filename'),
                latest_transformation.c.type.label('transformation_type'),
                latest_transformation.c.created_at.label('transformation_timestamp'),
            )
            .select_from(images_table)
            .join(subq, images_table.c.id == subq.c.image_id, isouter=True)  # noqa
            .join(
                latest_transformation,
                (latest_transformation.c.image_id == subq.c.image_id)
                & (latest_transformation.c.created_at == subq.c.max_created_at),
                isouter=True,
            )
            .order_by(latest_transformation.c.created_at.desc())
        )

        tuples = self.session.execute(query).all()
        data = [
            dict(
                zip(
                    [
                        'id',
                        'original_filename',
                        'transformation_type',
                        'transformation_timestamp',
                    ],
                    values,
                )
            )
            for values in tuples
        ]
        return TypeAdapter(list[TransformedImage]).validate_python(data)
