import asyncio
import os
import threading
from io import IOBase
from math import ceil
from urllib.request import urlopen, Request

from fsspec.implementations.cached import CachingFileSystem
from tqdm import tqdm

_WINDOWS = os.name == 'nt'

COPY_BUFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024


def _informed_copyfileobj(fsrc, fdst, total_bytes, silent=True):
    assert total_bytes, 'total_bytes must exists'
    total_chunks = ceil(int(total_bytes) / COPY_BUFSIZE)
    # Localize variable access to minimize overhead.
    fsrc_read = fsrc.read
    fdst_write = fdst.write
    total_chunks = range(total_chunks)
    if not silent:
        total_chunks = tqdm(total_chunks)
    for _ in total_chunks:
        if not threading.main_thread().is_alive():
            break
        buf = fsrc_read(COPY_BUFSIZE)
        if not buf:
            break
        fdst_write(buf)


def _copyfileobj(fsrc, fdst, length=0):
    """copy data from file-like object fsrc to file-like object fdst"""
    if not length:
        length = COPY_BUFSIZE
    # Localize variable access to minimize overhead.
    fsrc_read = fsrc.read
    fdst_write = fdst.write
    while True:
        if not threading.main_thread().is_alive():
            break
        buf = fsrc_read(length)
        if not buf:
            break
        fdst_write(buf)


def _fetch_file_impl(url, dst, headers, silent=True):
    with urlopen(Request(url, headers=headers)) as response:
        meta = response.info()  # HEAD
        content_len = meta['Content-Length']
        if content_len:  # Missing header, we are unable to determine total chunks
            if isinstance(dst, str) or isinstance(dst, os.PathLike):
                with open(dst, 'wb') as f:
                    _informed_copyfileobj(response, f, content_len, silent)
            if isinstance(dst, IOBase):
                _informed_copyfileobj(response, dst, content_len, silent)
        else:
            _copyfileobj(response, dst)


async def fetch_file(
    url,
    dst: str | IOBase | os.PathLike,
    key=None,
    key_name='Authorization',
    silent=True,
):
    assert (
        isinstance(dst, str) or isinstance(dst, IOBase) or isinstance(dst, os.PathLike)
    ), f'Invalid destination of type({type(dst)})'
    headers = {}
    if key:
        headers.update({key_name: key})

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _fetch_file_impl, url, dst, headers, silent)


def populate_filecache(remote_path: str, fs: CachingFileSystem):
    assert isinstance(
        fs, CachingFileSystem
    ), 'fs must be an instance of CachingFileSystem'
    assert fs.exists(remote_path), f'{remote_path} must exists'

    # Populate the KnownPartsOfAFile cache
    # Read a portion of the Parquet file (you can adjust the chunk size as needed)
    with fs.open(remote_path, 'rb') as f:
        while True:
            chunk = f.read(COPY_BUFSIZE)
            if not chunk:
                break  # Reached end of file


__all__ = ['fetch_file', 'populate_filecache']
