from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from dishka.integrations.faststream import setup_dishka

from faststream.asgi import AsgiFastStream, make_ping_asgi
from faststream.rabbit import RabbitBroker
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from corelib import constants
from corelib.web.config import get_settings
from connectinno.bootstrap import bootstrap, bootstrap_sync
from connectinno.drivers.mq.v1 import router as v1_router

_settings = get_settings()

container = bootstrap_sync(essential_only=_settings.DEBUG, di_sync=False)

broker = RabbitBroker()  # Important to instantiate with empty url in order to conceal actual bootstrap server URL

broker.include_router(v1_router)


async def on_app_startup():
    await broker.connect(_settings.RABBITMQ_URL)
    await bootstrap(container, False)  # type: ignore
    if _settings.SENTRY_DSN not in constants.EMPTY_VALUES:
        sentry_sdk.init(
            dsn=_settings.SENTRY_DSN,
            integrations=[
                RedisIntegration(),
                AsyncioIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=1.0,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=1.0,
        )


@asynccontextmanager
async def lifespan():
    await on_app_startup()
    yield


app = AsgiFastStream(
    broker,
    lifespan=lifespan,
    asyncapi_path=f'{_settings.ROOT_PATH}/docs',
    asgi_routes=[
        ('/api/v1/misc/health', make_ping_asgi(broker, timeout=5.0)),
    ],
)

setup_dishka(container, app)

__all__ = [
    'app',
]

if __name__ == '__main__':
    kwargs = dict(
        app_import_path='startup.entrypoints.stream:app',
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
