from outcome.pypicloud_storage_gcs import ThreadsafeGoogleCloudStorage
from pypicloud.storage.gcs import GoogleCloudStorage


# We need this dummy test so that the CI process doesn't complain
# due to a lack of tests
def test_dummy():
    assert issubclass(ThreadsafeGoogleCloudStorage, GoogleCloudStorage)
