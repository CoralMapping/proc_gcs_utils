## Google Cloud Storage (GCS) Utilities
This project provides a few simple utility functions for interacting with GCS.

### Authentication
To function properly, this code needs credentials that it can use to authenticate against the Google Cloud Storage API.  Credentials can be provided in one of two ways, and the code will look for them in this order:

1. Service Account Key.

Before running this code, create an environment variable named `SERVICE_ACCOUNT_KEY` containing the JSON key for a Google Cloud service account with the necessary permissions to perform the actions you're trying to perform in GCS.

2. Personal Credentials.

Before running this code, authenticate with the Google Cloud Storage API using the `gcloud` command line tool:
```
$ gcloud auth application-default login --project GCP_PROJECT_NAME
```

### Development

This project uses [Pipenv](https://docs.pipenv.org/en/latest/) to manage virtual environments and dependencies. Development-time dependencies are documented in the `Pipfile`. Follow the `Pipenv` documentation to create a virtual environment and install the dependencies.

This project also uses [pre-commit](https://pre-commit.com/) to run various Python code quality checks (linting and styling) on every commit.  Before you begin any development work, install the pre-commit hook with:

```bash
$ pre-commit install
```

#### Makefile

The included `Makefile` prescribes actions to test, build, and publish this code to a Python Package Index (PyPI) repository as described in the following sections.
```
$ make [test | build | publish]
```

#### Testing

With the virtual environment active and the dependencies installed, use [pytest](https://docs.pytest.org/en/latest/) to run the test suite.

The integration tests interact with the actual GCS API to manipulate blobs in an actual GCS bucket. If needed, change the GCS project and bucket used for these tests by changing the variables in the `test_gcs.py` module.

The integration tests require credentials for the GCS bucket that is used for testing. When running the tests, you must provide credentials as described in the Authentication section above.

To run only the unit tests, and skip the integration tests, run:
```
$ pipenv run pytest -m "not integration"
```

#### Building

This project uses the [setuptools](https://packaging.python.org/key_projects/#setuptools) Python package for packaging as described [here](https://packaging.python.org/tutorials/packaging-projects/).

When building via the `make build` command, you may optionally append to the package name using the `prerelease` argument. For example, if the current version of `gcsutils` specified in the `setup.py` module is `1.2.3`, then
```
$ make build prerelease=rc1
```
will produce a package named `gcsutils-1.2.3rc1`. The default is a beta prerelease name incremented by each git commit (eg/ `1.2.3b7` for the seventh commit on this branch). Specify a final release with
```
$ make build prerelease=""
```

Note that prerelease names must comply with [PEP 440](https://www.python.org/dev/peps/pep-0440/).

#### Publishing
This project uses the [twine](https://packaging.python.org/key_projects/#twine) Python package for distribution as described [here](https://packaging.python.org/tutorials/packaging-projects/).

When publishing via the `make publish` command, the default PyPI repository is [testpypi](https://packaging.python.org/guides/using-testpypi/). To publish to [pypi.org](https://pypi.org), specify that repository:
```
$ make publish pypi_repository=pypi
```

The credentials necessary to publish to the target PyPI repository can be provided in one of two ways.

1. As these environment variables:

| Env Var                      | Notes                                      |
| :--------:                   | ------------------------------------------ |
| `PYPI_REPOSITORY_USERNAME`   | PyPI account username. If authenticating [using a token](https://test.pypi.org/help/#apitoken), use the literal string `__token__`. |
| `PYPI_REPOSITORY_PASSWORD`   | PyPI account password. If authenticating [using a token](https://test.pypi.org/help/#apitoken), use the token contents. |

2. At the `make publish` command:
```
$ make publish pypi_repository_password="foo" pypi_repository_password="bar"
```
