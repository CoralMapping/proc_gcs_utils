## Google Cloud Storage (GCS) Utilities
This project provides a few simple utility functions for interacting with GCS.

### Installation
This package is hosted on a private Python Package Index (PyPi) repository. Before installing it, add this `source` to your Pipfile:

```
[[source]]
name = "pypi-coral-atlas"
url = "https://coral-atlas-pip-read:'${PYPI_REPOSITORY_PASSWORD}'@vulcin.jfrog.io/artifactory/api/pypi/pypi-coral-atlas/simple"
verify_ssl = true
```

As the source indicates, a password with read permissions on the PyPi repository is expected to be provided via the `PYPI_REPOSITORY_PASSWORD` environment variable.  This password is stored in Vault, so set the environment variable with this command:

```
$ export PYPI_REPOSITORY_PASSWORD="$(vault read --field=value coral-atlas/main/pypi-coral-atlas-read)"
```

Once the source has been added to your Pipfile, install the package like any other:

```
$ pipenv install proc_gcs_utils = "==0.0.1"
```

### Authentication
To function properly, this code needs credentials that it can use to authenticate against the Google Cloud Storage API.  Credentials can be provided in one of two ways, and the code will look for them in this order:

1. Service Account Key.

Before running this code, create an environment variable named `SERVICE_ACCOUNT_KEY` containing the JSON key for a Google Cloud service account with the necessary permissions to perform the actions you're trying to perform in GCS.

2. Personal Credentials.

Before running this code, authenticate with the Google Cloud Storage API using the `gcloud` command line tool:
```
$ gcloud auth application-default login --project GCP_PROJECT_NAME
```
