import asyncio
import hashlib
from contextlib import suppress
from typing import Optional, Dict

from redis.asyncio import Redis as AsyncRedis
from aio_pika.exceptions import CONNECTION_EXCEPTIONS
from fastapi import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2, APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from corelib.web.config import get_settings
from connectinno.di.keys import KeysGenerator
from connectinno.proxy import StartupProxy


async def _authenticate(proxy: StartupProxy, token: str):
    res = await proxy.authenticate(token=token)
    if res:
        return res['valid']
    return False


async def _check_api_key(api_key: str):
    return (
        hashlib.sha256(api_key.encode(), usedforsecurity=True).hexdigest()
        == get_settings().API_KEY
    )


class ExternalOAuth2Authorization(OAuth2):
    def __init__(
        self,
        token_url: str,
        validation_url: Optional[str] = None,
        refresh_url: Optional[str] = None,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={
                'tokenUrl': token_url,
                'refreshUrl': refresh_url,
                'validateUrl': validation_url,
                'scopes': scopes,
            }
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        client: AsyncRedis = request.state.dishka_container.get(AsyncRedis)
        proxy: StartupProxy = request.state.dishka_container.get(StartupProxy)
        _settings = get_settings()
        if not _settings.ACTIVATE_AUTHORIZATION:
            return None
        authorization: str = request.headers.get('Authorization')
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != 'bearer':
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail='Not authenticated',
                    headers={'WWW-Authenticate': 'Bearer'},
                )
            else:
                return None
        param = str(param)
        auth_key = KeysGenerator.instance.auth_token(param)
        rjson = await client.json()
        payload = await rjson.get(auth_key)
        if payload is not None:
            return param
        res = await _authenticate(proxy, param)
        e = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        if not res:
            raise e
        try:
            payload = await proxy.get_user_info(token=param)
            await rjson.set(auth_key, '.', payload['user_data'])
            asyncio.ensure_future(
                client.expire(auth_key, time=_settings.AUTH_TOKEN_CACHE_EXPIRE)
            )
            return param
        except RuntimeError:
            raise e
        except CONNECTION_EXCEPTIONS:
            raise e


class APIKeyAuthorization(APIKeyHeader):
    async def __call__(self, request: Request) -> Optional[str]:
        _settings = get_settings()
        if not _settings.ACTIVATE_AUTHORIZATION:
            return None
        api_key = request.headers.get(self.model.name)
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail='Not authenticated'
                )
            else:
                return None

        with suppress(Exception):
            if await _check_api_key(api_key):
                return api_key

        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail='Could not validate credentials'
        )


__all__ = ['ExternalOAuth2Authorization', 'APIKeyAuthorization']
