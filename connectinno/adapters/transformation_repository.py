from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count

from connectinno.ports.repository import IRepository
from connectinno.infra.db.alchemy.models.transformation import (
    transformations_table,
)
from connectinno.ports.repository import ObjectDoesNotExists
from domain.entities import BaseTransformation
from domain.value_objects.transformation_stat import TransformationByType


class TransformationRepository(IRepository):
    def __init__(self, session: Session):
        self.session = session
        self.seen = set()

    def get(self, ref: int) -> BaseTransformation:
        result = self.session.execute(
            select(BaseTransformation).where(transformations_table.c.id == ref)
        )
        result = result.scalars().all()
        if not result:
            raise ObjectDoesNotExists()
        obj = result[0]
        self.seen.add(obj)
        return obj

    def add(self, transformation: BaseTransformation):
        self.session.add(transformation)
        self.seen.add(transformation)

    def count_transformation_by_type(self) -> list[TransformationByType]:
        c = count(transformations_table.c.id)
        stmt = (
            select(c, transformations_table.c.type)
            .group_by(transformations_table.c.type)
            .order_by(c.desc())
        )
        tuples = self.session.execute(stmt).all()
        data = [dict(zip(['count', 'type'], values)) for values in tuples]
        return TypeAdapter(list[TransformationByType]).validate_python(data)
