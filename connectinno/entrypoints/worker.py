import os
import sys
import warnings

from celery import signals
from sentry_sdk import init as init_sentry
from sentry_sdk.integrations.celery import CeleryIntegration

from corelib.celery.config import build_application
from connectinno.bootstrap import bootstrap_sync

app = build_application(__name__)
container = bootstrap_sync(essential_only=True)
app.dishka_container = container

# Load task modules
app.autodiscover_tasks(
    [
        'corelib',
        'connectinno.drivers.celery',
    ],
    force=True,
)


@signals.celeryd_init.connect
def on_celery_init(sender, instance, conf, options, **kwargs):  # noqa
    sentry_dsn = conf.get('SENTRY_DSN', None)
    if sentry_dsn:
        init_sentry(
            dsn=sentry_dsn,
            integrations=[
                CeleryIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production,
            traces_sample_rate=conf.get('sentry_traces_sample_rate', 1.0),
        )


@signals.worker_init.connect
def on_worker_init(*args, **kwargs):
    warnings.filterwarnings('ignore')
    sys.path.insert(0, os.getcwd())  # module import fixups


if __name__ == '__main__':
    worker = app.Worker()
    worker.start()
