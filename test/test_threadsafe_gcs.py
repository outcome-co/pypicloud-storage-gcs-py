import time
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from unittest.mock import Mock, patch

import pytest
from outcome.pypicloud_storage_gcs.threadsafe_gcs import BucketDescriptor

bucket_name = 'test_bucket'
kwargs = {'arg': 'value'}


mock_gcs_client_factory = Mock()


def mock_gcs_client_factory_implementation(*args, **kwargs):
    mock_client = Mock()
    mock_bucket = Mock()

    mock_bucket.client = mock_client
    mock_client.bucket.return_value = mock_bucket

    return mock_client


mock_gcs_client_factory.side_effect = mock_gcs_client_factory_implementation


@pytest.fixture(autouse=True)
def reset_mock():
    mock_gcs_client_factory.reset_mock()
    mock_gcs_client_factory.side_effect = mock_gcs_client_factory_implementation


class DummyClass:
    bucket = BucketDescriptor(mock_gcs_client_factory)

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

        mock_gcs_client_factory.assert_not_called()

        bucket_a = instance.bucket
        bucket_b = instance.bucket

        assert bucket_a is bucket_b
        mock_gcs_client_factory.assert_called_once_with(kwargs)

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
