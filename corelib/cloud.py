import functools
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import FilePath


class CloudSettings(BaseSettings):
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None

    GCS_BUCKET_NAME: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[FilePath] = None


@functools.cache
def get_cloud_settings():
    return CloudSettings()
