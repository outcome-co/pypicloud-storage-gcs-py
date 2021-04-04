import time
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from typing import Callable, Iterable, Protocol, Sequence, TypeVar, cast
from unittest.mock import Mock

from outcome.pypicloud_storage_gcs.threadsafe_gcs import Bucket, Client, Settings, ThreadsafeGoogleCloudStorage

bucket_name = 'test_bucket'
settings = {'arg': 'value'}


def get_bucket_id(bucket: Bucket) -> int:
    # We sleep to ensure that we don't re-use the same thread/process
    # twice
    time.sleep(0.5)

    # We return the object id of the bucket's client, since we can't return the
    # actual bucket as it doesn't pickle
    return id(cast(Client, bucket.client))


T = TypeVar('T')


class IsolatedStorage(ThreadsafeGoogleCloudStorage):
    @classmethod
    def _get_storage_client(cls, settings: Settings) -> Client:
        return Mock()


class Pool(Protocol):
    def close(self) -> None:
        ...

    def join(self) -> None:
        ...

    def map(self, func: Callable[[T], object], iterable: Iterable[T]) -> Sequence[object]:  # noqa: A003
        ...


class PoolConstructor(Protocol):
    def __call__(self, processes: int) -> Pool:
        ...


class TestThreadsafe:
    def test_single_thread(self):
        bucket = IsolatedStorage.get_bucket(bucket_name, settings, skip_default=True)
        assert bucket.client is bucket.client

    def run_pool_test(self, pool_type: PoolConstructor):
        bucket = IsolatedStorage.get_bucket(bucket_name, settings, skip_default=True)

        parallelism = 4
        parallel_args = [bucket] * parallelism  # noqa: WPS435

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
