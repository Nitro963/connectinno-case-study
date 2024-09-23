import warnings
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from starlette.middleware.cors import CORSMiddleware

from corelib import constants
from corelib.web import patches
from corelib.web.config import get_settings
from connectinno.ports.repository import ObjectDoesNotExists
from connectinno.bootstrap import bootstrap, bootstrap_sync
from connectinno.drivers.api import errors
from connectinno.drivers.api.v1 import router as v1_router

_settings = get_settings()

container = bootstrap_sync(essential_only=True, di_sync=False)


async def on_app_startup(api: FastAPI):
    warnings.filterwarnings('ignore')
    await bootstrap(api.state.dishka_container, True)  # type: ignore
    if _settings.SENTRY_DSN not in constants.EMPTY_VALUES:
        sentry_sdk.init(
            dsn=_settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                RedisIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=1.0,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=1.0,
        )


async def on_app_shutdown(api: FastAPI):
    container: AsyncContainer = api.state.dishka_container  # noqa
    await container.close()
    # Add clean up functions
    # cuda.empty_cache()


@asynccontextmanager
async def lifespan(api: FastAPI):
    await on_app_startup(api)
    yield
    await on_app_shutdown(api)


app = FastAPI(
    root_path=_settings.ROOT_PATH,
    title=_settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url='/api/openapi.json',
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=_settings.BACKEND_CORS_ORIGINS or ['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_exception_handler(
    NotImplementedError, patches.not_implemented_exception_handler
)
app.add_exception_handler(TimeoutError, patches.timeout_exception_handler)
app.add_exception_handler(ObjectDoesNotExists, errors.does_not_exists_exception_handler)

setup_dishka(container, app)

app.include_router(v1_router)

__all__ = [
    'app',
]

if __name__ == '__main__':
    kwargs = dict(
        app_import_path='startup.entrypoints.asgi:app',
        host='127.0.0.1',
        port=8080,
        log_config='uvicorn-logging-config.json',
    )

    if _settings.DEBUG:
        kwargs.update(
            dict(
                reload=bool(_settings.DEBUG),
                reload_dirs=['./'],
                reload_excludes=[
                    'startup/drivers/api/*',
                ],
            )
        )
    uvicorn.run(**kwargs)
