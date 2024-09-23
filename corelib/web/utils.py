import asyncio
import functools
import logging
import os
import socket

import psutil

from ..recase import ReCase

logger = logging.getLogger('uvicorn.error')


def server_info():
    return {
        'hostname': socket.gethostname(),
        'cpu_usage': psutil.cpu_percent(),
        'cpu_core': psutil.cpu_count(),
        'memory_usage': psutil.virtual_memory().percent,
    }


def secure_filename(filename):
    r"""Pass it a filename, and it will return a secure version of it.  This
    filename can then safely be stored on a regular file system and passed
    to :func:`os.path.join`.  The filename returned is an ASCII only string
    for maximum portability.

    On Windows systems the function also makes sure that the file is not
    named after one of the special device files.

    >>> secure_filename('My cool movie.mov')
    'My_cool_movie.mov'
    >>> secure_filename('../../../etc/passwd')
    'etc_passwd'
    >>> secure_filename('I contain cool \xfcml\xe4uts.txt')
    'i_contain_cool_umlauts.txt'

    The function might return an empty filename.  It's your responsibility
    to ensure that the filename is unique and that you generate random
    filename if the function returned an empty one.

    . versionadded:: 0.5

    :param filename: the filename to secure
    """
    import re

    _filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')
    _windows_device_files = (
        'CON',
        'AUX',
        'COM1',
        'COM2',
        'COM3',
        'COM4',
        'LPT1',
        'LPT2',
        'LPT3',
        'PRN',
        'NUL',
    )
    if isinstance(filename, str):
        from unicodedata import normalize

        filename = normalize('NFKD', filename).encode('ascii', 'ignore')
        filename = filename.decode('ascii')

    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(filename.split()))).strip(
        '._'
    )

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    if (
        os.name == 'nt'
        and filename
        and filename.split('.')[0].upper() in _windows_device_files
    ):
        filename = '_' + filename

    return filename


def prefixed(*, use_func_type: bool):
    def decorator(f):
        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            return await f(*args, **kwargs)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        from .config import get_settings

        settings = get_settings()
        project_name = f'{ReCase(settings.PROJECT_NAME).snake_case}'
        func_type = 'sync'
        if asyncio.iscoroutinefunction(f):
            func_type = 'async'
        func_name = '::'.join(
            filter(
                lambda x: len(x.strip()) != 0,
                [project_name, func_type if use_func_type else '', wrapper.__name__],
            )
        )

        async_wrapper.__name__ = func_name
        wrapper.__name__ = func_name
        return wrapper if not asyncio.iscoroutinefunction(f) else async_wrapper

    return decorator


def format_as_sse(id_: int | str, event_type: str, data: str) -> str:
    """Construct a Server-Sent Event (SSE) string"""
    return f'event: {event_type}\ndata: {data}\nid: {id_}\n\n'
