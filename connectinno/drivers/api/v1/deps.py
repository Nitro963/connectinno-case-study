import asyncio
import os
import tempfile
from typing import Annotated

from celery import Celery
from fastapi import Depends, HTTPException
from redis import RedisError
from redis.asyncio import Redis as AsyncRedis
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from corelib.web.config import get_settings, Settings
from connectinno.di import FromDI
from connectinno.di.fastapi import inject
from connectinno.di.keys import KeysGenerator
from connectinno.drivers.api.schema.user_data import UserData
from connectinno.proxy import StartupProxy
from .security import ExternalOAuth2Authorization, APIKeyAuthorization

reusable_oauth2 = ExternalOAuth2Authorization(
    token_url='/login',
    validation_url='/token/validate',
    refresh_url='/token/refresh',
)

api_key_auth = APIKeyAuthorization(name='X-API-KEY')


def celery_app() -> Celery:
    from corelib.celery.config import build_application

    app = build_application(strict_typing=False)

    app.set_current()

    return app


# We need to initialize celery app in each running thread for `shared_task` decorator to work correctly
async def async_celery_app() -> Celery:
    from corelib.celery.config import build_application

    app = build_application(strict_typing=False)

    app.set_current()

    return app


@inject
async def get_current_user(
    client: FromDI[AsyncRedis],
    proxy: FromDI[StartupProxy],
    auth: str = Depends(reusable_oauth2),
) -> UserData:
    rjson = client.json()
    user_data = await rjson.get(KeysGenerator.instance.auth_token(auth))
    if user_data is not None:
        return UserData.model_validate(user_data)
    user_info = await proxy.get_user_info(token=auth)
    user_data = user_info.get('user_data', None)
    if user_data is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return UserData.model_validate(user_data)


async def temp_file():
    """Create (and finally delete) a temporary file in a safe and non-blocking fashion."""
    loop = asyncio.get_running_loop()
    _, path = await loop.run_in_executor(None, tempfile.mkstemp)
    return path


def remove_file(path: str) -> None:
    if os.path.exists(path):
        os.unlink(path)


class PermissionChecker:
    def __init__(self, permissions: set[str]):
        self.permissions = permissions

    @inject
    async def __call__(
        self,
        client: FromDI[AsyncRedis],
        settings: Annotated[Settings, Depends(get_settings)],
        user: Annotated[UserData, Depends(get_current_user)],
        proxy: FromDI[StartupProxy],
    ):
        rjson = client.json()
        perm_key = KeysGenerator.instance.user_has_permissions(
            user.auth_id, user.user_type
        )
        try:
            res = await rjson.get(perm_key, '.')
            if res and len(set(res).intersection(self.permissions)) == len(
                self.permissions
            ):
                return

            res = await proxy.get_user_permissions(
                user_id=int(user.auth_id), user_type=user.user_type.value
            )
            if len(set(res).intersection(self.permissions)) != len(self.permissions):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail='This action is unauthorized'
                )

            await rjson.set(perm_key, '.', res)
            asyncio.ensure_future(
                client.expire(perm_key, time=settings.AUTH_TOKEN_CACHE_EXPIRE)
            )
        except (RedisError, RuntimeError):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail='This action is unauthorized'
            )
