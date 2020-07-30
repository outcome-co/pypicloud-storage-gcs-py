from unittest.mock import patch, Mock

from outcome.pypicloud_storage_gcs.threadsafe_gcs import BucketDescriptor
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Pool as ProcessPool
import time


bucket_name = 'test_bucket'
kwargs = {'arg': 'value'}


class DummyClass:
    bucket = BucketDescriptor()

    def __init__(self):
        self.bucket_name = bucket_name
        self.bucket_client_settings = kwargs


def get_bucket_id(instance):
    # We sleep to ensure that we don't re-use the same thread/process
    # twice
    time.sleep(0.5)

    # We return the object id of the bucket's client, since we can't return the
    # actual bucket as it doesn't pickle
    return id(instance.bucket.client)


class TestDescriptor:

    @patch('outcome.pypicloud_storage_gcs.threadsafe_gcs.ThreadsafeGoogleCloudStorage._get_storage_client', autospec=True)
    def test_descriptor(self, mocked_get_client: Mock):
        instance = DummyClass()

        mocked_get_client.assert_not_called()

        bucket_a = instance.bucket
        bucket_b = instance.bucket

        assert bucket_a is bucket_b
        mocked_get_client.assert_called_once_with(kwargs)

    def run_pool_test(self, pool_type):
        instance = DummyClass()

        parallelism = 4
        parallel_args = [instance] * parallelism  # noqa: WPS435

        pool = pool_type(parallelism)
        results = pool.map(get_bucket_id, parallel_args)
        pool.close()
        pool.join()

        # Each thread/process should return a different key
        assert parallelism > 1
        assert len(set(results)) == parallelism

    def test_multithread(self):
        self.run_pool_test(ThreadPool)

    def test_multiprocess(self):
        self.run_pool_test(ProcessPool)
