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

from pypicloud.storage.gcs import GoogleCloudStorage

LOG = logging.getLogger(__name__)


class BucketDescriptor:
    def __init__(self, gcs_client_factory) -> None:
        self.bucket_map = {}
        self.gcs_client_factory = gcs_client_factory

    def __set__(self, obj, value):  # pragma: no cover
        # Turn obj.bucket = <some obj> into a no-op
        ...

    @staticmethod
    def get_key(obj):  # noqa: WPS602
        oid = id(obj)
        pid = os.getpid()
        tid = threading.get_native_id()
        return f'{pid}-{tid}-{oid}'

    def __get__(self, obj, objtype=None):
        # Get a unique combination of the process ID and thread ID
        # The values can be recycled, but we know the combination
        # will be unique at any given point in time
        key = self.get_key(obj)

        if key not in self.bucket_map:
            LOG.info('Creating the thread-specific GCS client with key %s', key)  # noqa: WPS323

            # Get the bucket name and settins from the object
            bucket_client_settings = obj.bucket_client_settings
            bucket_name = obj.bucket_name

            client = self.gcs_client_factory(bucket_client_settings)
            self.bucket_map[key] = client.bucket(bucket_name)
        else:
            LOG.info('Re-using the thread-specific GCS client with key %s', key)  # noqa: WPS323

        return self.bucket_map[key]


class ThreadsafeGoogleCloudStorage(GoogleCloudStorage):  # pragma: no cover

    # Set the bucket attribute to a descriptor, which allows for
    # property-like dynamic behaviour
    bucket = BucketDescriptor(GoogleCloudStorage._get_storage_client)

    def __init__(self, *args, **kwargs) -> None:
        # Keep the name of the bucket
        self.bucket_name = kwargs.get('bucket')
        self.bucket_client_settings = kwargs

        super().__init__(*args, **kwargs)

    @classmethod
    def get_bucket(cls, bucket_name: str, settings):
        LOG.info('Skipping pre-fork bucket initialisation')
        # We return the bucket name instead of the bucket
        # A bit of a hack, but the only way to get the bucket name
        # into the __init__ function
        return bucket_name
