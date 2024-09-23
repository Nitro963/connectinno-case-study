import logging
import os
import sys

from gunicorn import glogging


class GunicornLogger(glogging.Logger):
    access_fmt = '%(asctime)s [%(process)d] [%(levelname)s] %(message)s'
    datefmt = '[%Y-%m-%d %H:%M:%S %z]'

    def setup(self, cfg):
        super().setup(cfg)
        if cfg.accesslog is not None:
            self._set_handler(
                self.access_log,
                cfg.accesslog,
                fmt=logging.Formatter(self.access_fmt, datefmt=self.datefmt),
                stream=sys.stdout,
            )

        from .config import get_settings

        settings = get_settings()
        if settings.LOG_ERRORS_IN_FILES:
            handler = logging.FileHandler(
                os.path.join(settings.FILE_LOG_BASE, 'gunicorn.err')
            )  # noqa
            handler.setFormatter(
                logging.Formatter(self.error_fmt, datefmt=self.datefmt)
            )
            handler.setLevel(self.loglevel)
            self.error_log.addHandler(handler)
            handler = logging.FileHandler(
                os.path.join(settings.FILE_LOG_BASE, 'gunicorn.access')
            )  # noqa
            handler.setFormatter(
                logging.Formatter(self.access_fmt, datefmt=self.datefmt)
            )
            handler.setLevel(self.loglevel)
            self.access_log.addHandler(handler)
