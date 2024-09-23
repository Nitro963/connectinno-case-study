from sqlalchemy.orm import relationship

from connectinno.infra.db.alchemy.models.base import mapper_registry
from connectinno.infra.db.alchemy.models.image import images_table
from connectinno.infra.db.alchemy.models.user import users_table
from connectinno.infra.db.alchemy.models import transformation
from domain import entities


def start_mappers():
    # Map the class to the table
    mapper_registry.map_imperatively(entities.User, users_table)
    mapper_registry.map_imperatively(
        entities.ImageModel,
        images_table,
        properties={
            'transformations': relationship(
                entities.BaseTransformation, lazy='selectin', back_populates='image'
            )
        },
    )
    transformation_types_map = entities.transformation_types_map
    mapper_registry.map_imperatively(
        entities.BaseTransformation,
        transformation.transformations_table,
        properties={'image': relationship(entities.ImageModel, lazy='joined')},
        polymorphic_on=transformation.transformations_table.c.type,
        polymorphic_identity=transformation_types_map[entities.BaseTransformation],
    )

    mapper_registry.map_imperatively(
        entities.RotateTransformation,
        transformation.rotate_transformations_table,
        inherits=entities.BaseTransformation,
        polymorphic_identity=transformation_types_map[entities.RotateTransformation],
    )

    mapper_registry.map_imperatively(
        entities.GrayScaleTransformation,
        transformation.gray_scale_transformations_table,
        inherits=entities.BaseTransformation,
        polymorphic_identity=transformation_types_map[entities.GrayScaleTransformation],
    )

    mapper_registry.map_imperatively(
        entities.ResizeTransformation,
        transformation.resize_transformations_table,
        inherits=entities.BaseTransformation,
        polymorphic_identity=transformation_types_map[entities.ResizeTransformation],
    )
