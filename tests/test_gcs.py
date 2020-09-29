'''
 Copyright Vulcan Inc. 2018-2020

 Licensed under the Apache License, Version 2.0 (the "License").
 You may not use this file except in compliance with the License.
 A copy of the License is located at

     http://www.apache.org/licenses/LICENSE-2.0

 or in the "license" file accompanying this file. This file is distributed
 on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied. See the License for the specific language governing
 permissions and limitations under the License.
'''


import json
import os
import random
import string
import tempfile
from unittest.mock import MagicMock, patch

import google
import pytest

from gcsutils import gcs
from gcsutils.gcs import (_copy_blob,
                          copy_file,
                          download_file,
                          download_files,
                          gcs_join,
                          list_bucket_contents,
                          list_bucket_folders,
                          rename_file,
                          upload_file,
                          upload_files)


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

    @pytest.mark.parametrize('input,expected_path', [
        (['foo', ''], 'foo'),
        (['foo/', ''], 'foo'),
        (['foo', '', ''], 'foo')
    ])
    def test_no_extra_forward_slashes(self, input, expected_path):
        actual_path = gcs_join(input)
        assert actual_path == expected_path


class TestGetClient:

    def test_works_with_service_account_key(self):
        mock_storage = MagicMock()
        fake_client = MagicMock()
        mock_storage.Client.return_value = fake_client
        mock_os = MagicMock()
        fake_service_account_key = {'client_email': 'foo@bar.com'}
        mock_os.environ = {'SERVICE_ACCOUNT_KEY': json.dumps(fake_service_account_key)}
        mock_service_account = MagicMock()
        fake_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_info.return_value = fake_credentials
        with patch.multiple('gcsutils.gcs',
                            os=mock_os,
                            service_account=mock_service_account,
                            storage=mock_storage):
            actual_client = gcs._get_storage_client(GCP_PROJECT_NAME)

        assert actual_client == fake_client
        mock_service_account.Credentials.from_service_account_info.assert_called_once_with(fake_service_account_key)
        mock_storage.Client.assert_called_once_with(project=GCP_PROJECT_NAME,
                                                    credentials=fake_credentials)

    def test_clear_message_if_key_is_invalid_json(self):
        mock_os = MagicMock()
        fake_service_account_key = ''
        mock_os.environ = {'SERVICE_ACCOUNT_KEY': fake_service_account_key}
        with pytest.raises(ValueError) as e:
            with patch('gcsutils.gcs.os', mock_os):
                gcs._get_storage_client(GCP_PROJECT_NAME)

        expected_message = 'SERVICE_ACCOUNT_KEY is empty or contains invalid JSON'
        assert expected_message in e.exconly()

    def test_works_with_supplied_credentials_file(self):
        mock_storage = MagicMock()
        fake_client = MagicMock()
        mock_storage.Client.return_value = fake_client
        mock_os = MagicMock()
        mock_os.environ = {}
        mock_service_account = MagicMock()
        with patch.multiple('gcsutils.gcs',
                            os=mock_os,
                            service_account=mock_service_account,
                            storage=mock_storage):
            actual_client = gcs._get_storage_client(GCP_PROJECT_NAME)

        assert actual_client == fake_client
        mock_storage.Client.assert_called_once_with(project=GCP_PROJECT_NAME)
        mock_service_account.Credentials.from_service_account_info.assert_not_called()


class TestCopyBlob:

    fake_blob = 'my_fake_gcs_blob'
    fake_new_gcs_path = 'bogus/new/path/to/blob'

    def test_happy_path(self):
        mock_bucket = MagicMock()
        mock_bucket.copy_blob.side_effect = [
            google.api_core.exceptions.ServiceUnavailable('foo'),
            google.api_core.exceptions.ServiceUnavailable('foo'),
            None
        ]

        _copy_blob(self.fake_blob, mock_bucket, self.fake_new_gcs_path)

        assert len(mock_bucket.copy_blob.mock_calls) == 3

    def test_raises_after_five_retries(self):
        mock_bucket = MagicMock()
        mock_bucket.copy_blob.side_effect = google.api_core.exceptions.ServiceUnavailable('foo')

        with pytest.raises(google.api_core.exceptions.ServiceUnavailable):
            _copy_blob(self.fake_blob, mock_bucket, self.fake_new_gcs_path, retries=6)


@pytest.mark.integration
def test_gcs_bucket_upload_download():
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

        upload_files(GCP_PROJECT_NAME,
                     GCS_BUCKET_NAME,
                     GCS_BUCKET_PATH,
                     input_dir)

        with open(os.path.join(input_dir, filename2), 'w') as f:
            f.write(file_2_contents)

        upload_file(GCP_PROJECT_NAME,
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

            upload_files(GCP_PROJECT_NAME,
                         GCS_BUCKET_NAME,
                         gcs_join([GCS_BUCKET_PATH, TOO_DEEP_FOLDER_NAME]),
                         too_deep_dir)

            upload_files(GCP_PROJECT_NAME,
                         GCS_BUCKET_NAME,
                         gcs_join([GCS_BUCKET_PATH, TOO_DEEP_FOLDER_NAME, 'deeper_still']),
                         too_deep_dir)

            # Verify we can list the test files
            blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                         GCS_BUCKET_NAME,
                                         GCS_BUCKET_PATH)

            for blob in blobs:
                assert blob.name in [
                    gcs_join([GCS_BUCKET_PATH, f]) for f in [filename0, filename1, filename2]
                ]

            # Verify we can move a test file
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
            folders = list_bucket_folders(GCP_PROJECT_NAME,
                                          GCS_BUCKET_NAME,
                                          GCS_BUCKET_PATH)

            assert folders == [TOO_DEEP_FOLDER_NAME]

            # Verify we can download the test files
            output_dir = os.path.join(temp_path, 'out')
            os.mkdir(output_dir)

            # ...one at a time
            download_file(GCP_PROJECT_NAME,
                          GCS_BUCKET_NAME,
                          gcs_join([GCS_BUCKET_PATH, filename0]),
                          os.path.join(output_dir, filename0))

            with open(os.path.join(output_dir, filename0)) as f:
                assert f.read() == file_0_contents
            os.remove(os.path.join(output_dir, filename0))

            # ...all at once
            download_files(GCP_PROJECT_NAME,
                           GCS_BUCKET_NAME,
                           GCS_BUCKET_PATH,
                           output_dir)

            with open(os.path.join(output_dir, filename0)) as f:
                assert f.read() == file_0_contents
            with open(os.path.join(output_dir, filename1)) as f:
                assert f.read() == file_1_contents
            with open(os.path.join(output_dir, filename2)) as f:
                assert f.read() == file_2_contents

            # Verify raises ValueError if download file not found
            try:
                download_file(GCP_PROJECT_NAME,
                                       GCS_BUCKET_NAME,
                                       'file/does/not/exists.txt',
                                       os.path.join(output_dir, 'does_not_exist.txt'))
            except ValueError:
                pass

        finally:
            blobs = list_bucket_contents(GCP_PROJECT_NAME,
                                         GCS_BUCKET_NAME,
                                         GCS_BUCKET_PATH,
                                         recurse=True)
            for blob in blobs:
                blob.delete()
