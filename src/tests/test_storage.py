import os
import random
import string
import tempfile
from unittest.mock import patch

import pytest

from src.storage import (download_files_from_gcs,
                         list_bucket_contents,
                         upload_files_to_gcs)
from src.tests.test_data import TEST_SERVICE_ACCOUNT_KEY


GCP_PROJECT_NAME = 'coral-atlas'
GCS_BUCKET_NAME = 'coral-atlas-integration-tests'
GCS_BUCKET_PATH = 'test'


@pytest.mark.integration
def test_gcs_bucket_upload_download():
    test_environ = {
        'SERVICE_ACCOUNT_KEY': TEST_SERVICE_ACCOUNT_KEY
    }
    with tempfile.TemporaryDirectory() as temp_path:
        filename0 = ''.join(random.choices(string.ascii_letters, k=10))
        file_0_contents = 'This is file 0'
        filename1 = ''.join(random.choices(string.ascii_letters, k=10))
        file_1_contents = 'This is file 1'
        input_dir = os.path.join(temp_path, 'in')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, filename0), 'w') as f:
            f.write(file_0_contents)
        with open(os.path.join(input_dir, filename1), 'w') as f:
            f.write(file_1_contents)

        with patch('src.storage.os.environ', test_environ):
            upload_files_to_gcs(GCP_PROJECT_NAME,
                                GCS_BUCKET_NAME,
                                GCS_BUCKET_PATH,
                                input_dir)

        forbidden_file_name = 'forbidden_file'
        forbidden_file_contents = 'Do not return this file'
        forbidden_dir = os.path.join(input_dir, 'forbidden')
        os.mkdir(forbidden_dir)
        with open(os.path.join(forbidden_dir, forbidden_file_name), 'w') as f:
            f.write(forbidden_file_contents)

        with patch('src.storage.os.environ', test_environ):
            upload_files_to_gcs(GCP_PROJECT_NAME,
                                GCS_BUCKET_NAME,
                                GCS_BUCKET_PATH + '/forbidden',
                                forbidden_dir)

        with patch('src.storage.os.environ', test_environ):
            blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                         GCS_BUCKET_NAME,
                                         GCS_BUCKET_PATH)

        for blob in blobs:
            assert blob.name in [
                '{0}/{1}'.format(GCS_BUCKET_PATH, filename0),
                '{0}/{1}'.format(GCS_BUCKET_PATH, filename1)
            ]

        output_dir = os.path.join(temp_path, 'out')
        os.mkdir(output_dir)

        try:
            with patch('src.storage.os.environ', test_environ):
                download_files_from_gcs(GCP_PROJECT_NAME,
                                        GCS_BUCKET_NAME,
                                        GCS_BUCKET_PATH,
                                        output_dir)

            with open(os.path.join(output_dir, filename0)) as f:
                assert f.read() == file_0_contents
            with open(os.path.join(output_dir, filename1)) as f:
                assert f.read() == file_1_contents
        finally:
            with patch('src.storage.os.environ', test_environ):
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             GCS_BUCKET_PATH,
                                             recurse=True)
            for blob in blobs:
                blob.delete()
