import dataclasses
import shutil
from io import IOBase
from typing import Optional
from fsspec import AbstractFileSystem


class Registry:
    @dataclasses.dataclass
    class Entry:
        location: str
        fs: AbstractFileSystem

    def __init__(self, bind: AbstractFileSystem):
        self._fs = bind
        self._known_files: list = []

    def add(self, location: str, buff: IOBase, fs: Optional[AbstractFileSystem] = None):
        assert isinstance(buff, IOBase), 'buff must be IOBase instance'
        assert fs or self._fs, 'fs must exists'
        fs = fs or self._fs
        with fs.open(location, 'wb') as dst:
            shutil.copyfileobj(buff, dst)
        self._known_files.append(self.Entry(location=location, fs=fs))

    def remove(self, location):
        self._fs.rm(location)

    def commit(self):
        self._known_files.clear()

    def rollback(self):
        for entry in self._known_files:
            try:
                entry.fs.rm(entry.location)
            except FileNotFoundError:
                pass
