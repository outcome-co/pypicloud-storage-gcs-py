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

from pypicloud.storage.gcs import GoogleCloudStorage

LOG = logging.getLogger(__name__)


class ThreadsafeGoogleCloudStorage(GoogleCloudStorage):  # pragma: no cover
    def __init__(self, *args, **kwargs) -> None:
        # Wait until we've created the instance, i.e. in the worker
        # thread, before creating the client instance
        LOG.info('Creating the thread-specific GCS client')
        client = self._get_storage_client(kwargs)
        kwargs['bucket'] = client.bucket(kwargs.get('bucket'))

        super().__init__(*args, **kwargs)

    @classmethod
    def get_bucket(cls, bucket_name: str, settings):
        LOG.info('Skipping pre-fork bucket initialisation')

        # This is a bit of a hack, the method is supposed to return
        # a bucket instance, instead we'll return the name of the
        # bucket and use it to create a thread/process-specific
        # instance in the class instance
        return bucket_name
