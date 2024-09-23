from enum import Enum

EMPTY_VALUES = (None, '', [], (), {})
UUID_REGEX = r'^[-a-fA-F0-9]+$'
ARCHIVE_REGEX = r'^[-a-fA-F0-9]+\.zip$'


class Environments(str, Enum):
    dev = 'DEV'
    stage = 'STAGE'
    prod = 'PROD'

    def __repr__(self):
        return self.value
