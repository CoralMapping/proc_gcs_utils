## Google Cloud Storage (GCS) Utilities
This project provides a few simple utility functions for interacting with GCS.

### Installation
To install a specific version of this library, add this line to the `requires` section of your `Pipfile`, substituting a release tag (or, in rare circumstances, a git commit SHA) in place of `VERSION`:

```
proc-gcs-utils = {editable = true,git = "https://github.com/CoralMapping/proc_gcs_utils.git",ref = "[VERSION]"}
```

### Authentication
This code expects an environment variable named `SERVICE_ACCOUNT_KEY` to exist and contain the JSON key for a Google Cloud service account with the necessary permissions to perform the actions you're trying to perform in GCS.
