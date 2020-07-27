# pypicloud-storage-gcs-py
![ci-badge](https://github.com/outcome-co/pypicloud-storage-gcs-py/workflows/Release/badge.svg) ![version-badge](https://img.shields.io/badge/version-0.2.0-brightgreen)

A fork-safe verion of the GCS Storage backend.

The GCS library uses `requests` to handle HTTP/S calls, but the SSL-state management inside `requests` doesn't handle os.fork calls very well. By default, the pypicloud GCS storage adapter creates the client before forking, so the same GCS client gets used across multiple processes which leads to issues.

This replacement defers the creation of the GCS client until the process has been forked.

## Usage

### Installation

```sh
poetry add outcome-pypicloud-storage-gcs
```

### Configuration

To use the storage backend, configure it in the `server.ini`. The settings/options for the adapter are identical to those for the original adapter.

```ini
# Set up GCS storage
pypi.storage = outcome.pypicloud_storage_gcs.ThreadsafeGoogleCloudStorage
storage.bucket = my-bucket
```

## Development

Remember to run `./pre-commit.sh` when you clone the repository.
