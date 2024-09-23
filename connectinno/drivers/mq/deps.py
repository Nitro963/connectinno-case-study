from celery import Celery


async def async_celery_app() -> Celery:
    from corelib.celery.config import build_application

    app = build_application(strict_typing=False)

    app.set_current()

    return app
