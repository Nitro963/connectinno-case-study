import datetime
from typing import Literal

from botocore.client import BaseClient
from google.cloud import storage

from pydantic import BaseModel, ConfigDict


class StorageServiceProxy(BaseModel):
    bucket: str
    signature_expires_in: int = 3600
    client: storage.Client | BaseClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def generate_signed_url(self, location: str, method: Literal['GET', 'PUT']):
        loc = -1
        if location.startswith('gs://') or location.startswith('s3://'):
            loc = 2
        elif location.startswith('/'):
            loc = 1
        elif location.startswith(self.bucket):
            loc = 0

        if loc != -1:
            parts = location.split('/')
            assert parts[loc] == self.bucket, 'buckets must match'
            loc = loc + 1
            location = ''.join(parts[loc:])
        match self.client:
            case storage.Client():
                bucket = self.client.bucket(self.bucket)
                blob = bucket.blob(location)
                return blob.generate_signed_url(
                    expiration=datetime.timedelta(seconds=self.signature_expires_in),
                    method=method,
                )
            case BaseClient():
                match method:
                    case 'GET':
                        return self.client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': self.bucket, 'Key': location},
                            ExpiresIn=self.signature_expires_in,
                        )
                    case 'PUT':
                        return self.client.generate_presigned_url(
                            'put_object',
                            Params={'Bucket': self.bucket, 'Key': location},
                            ExpiresIn=self.signature_expires_in,
                        )

    async def agenerate_signed_url(self, location: str, method: Literal['GET', 'PUT']):
        raise NotImplementedError()
