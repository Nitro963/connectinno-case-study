import pathlib
from io import BytesIO
from typing import Annotated
from uuid import uuid4

import PIL.Image
from firebase_admin import App as FirebaseApp
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Path, UploadFile, File
from pydantic import TypeAdapter

from connectinno.app.cv import Transformer, strategy_from_model
from connectinno.app.unit_of_work import AbstractUnitOfWork
from connectinno.di import FromDI
from connectinno.drivers.api.schema.v1.image import ImageInfo
from corelib.web.constants import HTTP_422_NOT_FOUND_EXCEPTION
from domain.aggregates.image import ImageAggregate
from domain.commands.transform_image import TransformImageCommand
from domain.entities.image import ImageUrl, RankedImage, ImageModel, TransformedImage
from domain.value_objects.transformation_stat import TransformationByType
from fileslib.storage_service_proxy import StorageServiceProxy

router = APIRouter()


@router.get('/get-image/{image_id}', response_model=ImageUrl, status_code=200)
@inject
async def get_image(
    image_id: Annotated[int, Path()],
    uow: FromDI[AbstractUnitOfWork],
    proxy: FromDI[StorageServiceProxy],
):
    with uow:
        aggregate: ImageAggregate = uow.images.get(image_id)
        location = aggregate.image_info.location
    return {'id': image_id, 'url': proxy.generate_signed_url(location, 'GET')}


@router.get('/rank-images', status_code=200)
@inject
async def rank_image(uow: FromDI[AbstractUnitOfWork]) -> list[RankedImage]:
    with uow:
        data = uow.images.rank_images()
    return TypeAdapter(list[RankedImage]).validate_python(data)


@router.get('/transformation-by-type', status_code=200)
@inject
async def count_transformation_by_type(
    uow: FromDI[AbstractUnitOfWork],
) -> list[TransformationByType]:
    with uow:
        data = uow.transformations.count_transformation_by_type()
    return data


@router.get('/image-latest-transformations', status_code=200)
@inject
async def get_latest_transformations(
    uow: FromDI[AbstractUnitOfWork],
) -> list[TransformedImage]:
    with uow:
        data = uow.images.get_latest_transformations()
    return data


@router.post('/upload-image', status_code=201, response_model=ImageInfo)
@inject
async def upload_image(
    file: Annotated[UploadFile, File()],
    app: FromDI[FirebaseApp],
    uow: FromDI[AbstractUnitOfWork],
):
    with uow:
        buff = BytesIO()
        buff.write(await file.read())
        buff.seek(0)
        try:
            image_object = PIL.Image.open(buff)
            image_object.verify()
        except (IOError, SyntaxError):
            raise HTTP_422_NOT_FOUND_EXCEPTION
        buff.seek(0)
        location = f'{app.project_id}.appspot.com/{uuid4()}{pathlib.Path(file.filename).suffix}'
        uow.file_registry.add(location, buff)
        image = ImageModel(
            location=location, name=file.filename, transformation_count=0
        )
        aggregate: ImageAggregate = uow.images.add(image, image_object)
        uow.commit()
        return aggregate.image_info


@router.post('/transform-image', status_code=200, response_model=ImageInfo)
@inject
async def transform_image(
    command: TransformImageCommand,
    uow: FromDI[AbstractUnitOfWork],
    app: FromDI[FirebaseApp],
):
    with uow:
        aggregate: ImageAggregate = uow.images.get(command.image_id)
        aggregate = aggregate.load()

        transformations = [
            transformation.to_domain() for transformation in command.transformations
        ]

        transformed_image = aggregate.image
        transformer = Transformer()

        for obj in transformations:
            obj.image_id = command.image_id
            uow.transformations.add(obj)
            transformer.set_strategy(strategy_from_model(obj))
            transformed_image = transformer.transform(transformed_image)

        buff = BytesIO()
        transformed_image.save(buff, aggregate.image.format)
        buff.seek(0)

        old_file = aggregate.image_info.location
        location = (
            f'{app.project_id}.appspot.com/{uuid4()}{pathlib.Path(old_file).suffix}'
        )

        uow.file_registry.add(location, buff)
        aggregate.image_info.location = location
        uow.images.update(aggregate)
        uow.commit()

        # post-processing may happen in the background
        # but for simplicity will fire them up in the reqeust/response cycle
        uow.file_registry.remove(old_file)

        uow.images.sync_images_transformations()

        uow.commit()

        return aggregate.image_info
