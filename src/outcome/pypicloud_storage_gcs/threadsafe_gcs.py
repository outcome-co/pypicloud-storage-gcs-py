"""Fork-safe verion of the GCS Storage backend.

The GCS library uses `requests` to handle HTTP/S calls, but the SSL-state
management inside `requests` doesn't handle os.fork calls very well.
By default, the pypicloud GCS storage adapter creates the client before
forking, so the same GCS client gets used across multiple processes
which leads to issues.

This replacement defers the creation of the GCS client until the process
has been forked.
"""

import logging
import os
import threading
from typing import Callable, Dict, Iterator, Mapping, Optional, cast

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket
from google.cloud.storage.client import Client
from pypicloud.storage.gcs import GoogleCloudStorage

LOG = logging.getLogger(__name__)


Settings = Mapping[str, object]
ClientFactory = Callable[[Settings], Client]


class BucketProxy:
    bucket_name: str
    client_factory: ClientFactory
    settings: Settings
    client_map: Dict[str, Client]

    def __init__(self, bucket_name: str, client_factory: ClientFactory, settings: Settings) -> None:
        self.bucket_name = bucket_name
        self.client_factory = client_factory
        self.client_map = {}
        self.settings = settings

    @property
    def client(self) -> Client:
        return self._get_client()

    # We implement the subset of methods actually called by pypicloud

    def list_blobs(self, prefix: Optional[str] = None) -> Iterator[Blob]:  # pragma: no cover
        return cast(Iterator[Blob], self._get_client().list_blobs(bucket_or_name=self.bucket_name, prefix=prefix))

    def blob(self, name: str) -> Blob:  # pragma: no cover
        return self._get_bucket().blob(name)

    def _get_bucket(self) -> Bucket:  # pragma: no cover
        return self._get_client().bucket(self.bucket_name)

    def _get_client(self) -> Client:
        key = self._get_key()

        if key not in self.client_map:
            LOG.info('Creating the thread-specific GCS client with key %s', key)  # noqa: WPS323

            self.client_map[key] = self.client_factory(self.settings)
        else:
            LOG.info('Re-using the thread-specific GCS client with key %s', key)  # noqa: WPS323

        return self.client_map[key]

    def _get_key(self) -> str:
        oid = id(self)
        pid = os.getpid()
        tid = threading.get_native_id()
        return f'{pid}-{tid}-{oid}'


class ThreadsafeGoogleCloudStorage(GoogleCloudStorage):  # pragma: no cover
    @classmethod
    def get_bucket(cls, bucket_name: str, settings: Settings, skip_default: Optional[bool] = False) -> Bucket:
        # Call the super, as this allows the default implementation to create the bucket
        # if necessary
        if not skip_default:
            super().get_bucket(bucket_name, settings)

        return cast(Bucket, BucketProxy(bucket_name, cast(ClientFactory, cls._get_storage_client), settings))
