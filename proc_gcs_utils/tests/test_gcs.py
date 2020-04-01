import os
import random
import string
import tempfile
from unittest.mock import patch

import pytest

from proc_gcs_utils.gcs import (copy_file,
                                download_file_from_gcs,
                                download_files_from_gcs,
                                gcs_join,
                                list_bucket_contents,
                                list_bucket_folders,
                                rename_file,
                                upload_file_to_gcs,
                                upload_files_to_gcs)
from proc_gcs_utils.tests.test_data import TEST_SERVICE_ACCOUNT_KEY


GCP_PROJECT_NAME = 'coral-atlas'
GCS_BUCKET_NAME = 'coral-atlas-integration-tests'
GCS_BUCKET_PATH = 'path/to/test/data'
TOO_DEEP_FOLDER_NAME = 'too_deep'


class TestGcsJoin:

    @pytest.mark.parametrize('include_protocol,expected_path', [
        (False, 'path/to/bogus/file.txt'),
        (True, 'gs://path/to/bogus/file.txt')
    ])
    def test_gcs_join(self, include_protocol, expected_path):
        path_components = ['path', 'to', 'bogus', 'file.txt']
        actual = gcs_join(path_components, include_protocol)

        assert actual == expected_path

    def test_raises_if_no_path_segments_provided(self):
        with pytest.raises(ValueError):
            gcs_join([])


@pytest.mark.integration
def test_gcs_bucket_upload_download():
    test_environ = {
        'SERVICE_ACCOUNT_KEY': TEST_SERVICE_ACCOUNT_KEY
    }
    with tempfile.TemporaryDirectory() as temp_path:

        # Upload some files that we should read for this test
        filename0 = ''.join(random.choices(string.ascii_letters, k=10))
        file_0_contents = 'This is file 0'
        filename1 = ''.join(random.choices(string.ascii_letters, k=10))
        file_1_contents = 'This is file 1'
        filename2 = ''.join(random.choices(string.ascii_letters, k=10))
        file_2_contents = 'This is file 2'
        input_dir = os.path.join(temp_path, 'in')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, filename0), 'w') as f:
            f.write(file_0_contents)
        with open(os.path.join(input_dir, filename1), 'w') as f:
            f.write(file_1_contents)

        with patch('proc_gcs_utils.gcs.os.environ', test_environ):
            upload_files_to_gcs(GCP_PROJECT_NAME,
                                GCS_BUCKET_NAME,
                                GCS_BUCKET_PATH,
                                input_dir)

        with open(os.path.join(input_dir, filename2), 'w') as f:
            f.write(file_2_contents)

        with patch('proc_gcs_utils.gcs.os.environ', test_environ):
            upload_file_to_gcs(GCP_PROJECT_NAME,
                               GCS_BUCKET_NAME,
                               GCS_BUCKET_PATH,
                               os.path.join(input_dir, filename2))

        try:
            # Upload some files that should not be returned
            too_deep_file_name = 'too_deep_file'
            too_deep_file_contents = 'Do not return this file'
            too_deep_dir = os.path.join(input_dir, TOO_DEEP_FOLDER_NAME)
            os.mkdir(too_deep_dir)
            with open(os.path.join(too_deep_dir, too_deep_file_name), 'w') as f:
                f.write(too_deep_file_contents)

            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                upload_files_to_gcs(GCP_PROJECT_NAME,
                                    GCS_BUCKET_NAME,
                                    gcs_join([GCS_BUCKET_PATH, TOO_DEEP_FOLDER_NAME]),
                                    too_deep_dir)

                upload_files_to_gcs(GCP_PROJECT_NAME,
                                    GCS_BUCKET_NAME,
                                    gcs_join([GCS_BUCKET_PATH, TOO_DEEP_FOLDER_NAME, 'deeper_still']),
                                    too_deep_dir)

            # Verify we can list the test files
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             GCS_BUCKET_PATH)

            for blob in blobs:
                assert blob.name in [
                    gcs_join([GCS_BUCKET_PATH, f]) for f in [filename0, filename1, filename2]
                ]

            # Verify we can move a test file
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                rename_file(GCP_PROJECT_NAME,
                            GCS_BUCKET_NAME,
                            gcs_join([GCS_BUCKET_PATH, filename0]),
                            gcs_join([GCS_BUCKET_PATH, 'renamed', filename0]))

                # Find it in its new location
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             gcs_join([GCS_BUCKET_PATH, 'renamed']))
                contents = []
                for blob in blobs:
                    contents.append(blob.name)
                assert gcs_join([GCS_BUCKET_PATH, 'renamed', filename0]) in contents

                # Verify it was removed from its old location
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             GCS_BUCKET_PATH)
                contents = []
                for blob in blobs:
                    contents.append(blob.name)
                assert gcs_join([GCS_BUCKET_PATH, filename0]) not in contents

                # Move it back
                rename_file(GCP_PROJECT_NAME,
                            GCS_BUCKET_NAME,
                            gcs_join([GCS_BUCKET_PATH, 'renamed', filename0]),
                            gcs_join([GCS_BUCKET_PATH, filename0]))

            # Verify we can copy a test file
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                copy_file(GCP_PROJECT_NAME,
                          GCS_BUCKET_NAME,
                          gcs_join([GCS_BUCKET_PATH, filename0]),
                          gcs_join([GCS_BUCKET_PATH, 'copied', filename0]))

                # Find it in its new location
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             gcs_join([GCS_BUCKET_PATH, 'copied']))
                contents = []
                for blob in blobs:
                    contents.append(blob.name)
                assert gcs_join([GCS_BUCKET_PATH, 'copied', filename0]) in contents

                # Verify it also still exists in its old location
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             GCS_BUCKET_PATH)
                contents = []
                for blob in blobs:
                    contents.append(blob.name)
                assert gcs_join([GCS_BUCKET_PATH, filename0]) in contents

                # Move it back
                rename_file(GCP_PROJECT_NAME,
                            GCS_BUCKET_NAME,
                            gcs_join([GCS_BUCKET_PATH, 'copied', filename0]),
                            gcs_join([GCS_BUCKET_PATH, filename0]))

            # Verify we can list the subfolder(s) in the test data folder
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                folders = list_bucket_folders(GCP_PROJECT_NAME,
                                              GCS_BUCKET_NAME,
                                              GCS_BUCKET_PATH)

            assert folders == [TOO_DEEP_FOLDER_NAME]

            # Verify we can download the test files
            output_dir = os.path.join(temp_path, 'out')
            os.mkdir(output_dir)

            # ...one at a time
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                download_file_from_gcs(GCP_PROJECT_NAME,
                                       GCS_BUCKET_NAME,
                                       gcs_join([GCS_BUCKET_PATH, filename0]),
                                       os.path.join(output_dir, filename0))

            with open(os.path.join(output_dir, filename0)) as f:
                assert f.read() == file_0_contents
            os.remove(os.path.join(output_dir, filename0))


            # ...all at once
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                download_files_from_gcs(GCP_PROJECT_NAME,
                                        GCS_BUCKET_NAME,
                                        GCS_BUCKET_PATH,
                                        output_dir)

            with open(os.path.join(output_dir, filename0)) as f:
                assert f.read() == file_0_contents
            with open(os.path.join(output_dir, filename1)) as f:
                assert f.read() == file_1_contents
            with open(os.path.join(output_dir, filename2)) as f:
                assert f.read() == file_2_contents
        finally:
            with patch('proc_gcs_utils.gcs.os.environ', test_environ):
                blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                             GCS_BUCKET_NAME,
                                             GCS_BUCKET_PATH,
                                             recurse=True)
            for blob in blobs:
                blob.delete()
