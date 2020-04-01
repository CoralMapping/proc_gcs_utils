import asyncio
import json
import os
from typing import List

import google
from google.api_core.page_iterator import HTTPIterator
from google.cloud import storage
from google.oauth2 import service_account


def _get_credentials() -> service_account.Credentials:
    key = json.loads(os.environ['SERVICE_ACCOUNT_KEY'])
    credentials = service_account.Credentials.from_service_account_info(key)

    return credentials


def get_storage_bucket(gcp_project_name: str,
                       gcs_bucket_name: str) -> storage.bucket.Bucket:
    """Get a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name

    Returns:
      google.cloud.storage.bucket.Bucket instance
    """
    storage_client = storage.Client(project=gcp_project_name,
                                    credentials=_get_credentials())
    bucket = storage_client.bucket(gcs_bucket_name)

    return bucket


async def _upload_file_to_bucket(gcs_bucket: storage.bucket.Bucket,
                                 gcs_bucket_path: str,
                                 file_path: str) -> None:
    blob_name = os.path.join(gcs_bucket_path, os.path.basename(file_path))
    blob = gcs_bucket.blob(blob_name)
    blob.upload_from_filename(file_path)


def _get_file_paths_from_directory(directory: str) -> List[str]:
    file_paths = []
    for f in os.listdir(directory):
        file_path = os.path.join(directory, f)
        if os.path.isfile(file_path):
            file_paths.append(file_path)

    return file_paths


def _upload_files_to_bucket(gcp_project_name: str,
                            gcs_bucket_name: str,
                            gcs_bucket_path: str,
                            file_paths: List[str]) -> None:
    bucket = get_storage_bucket(gcp_project_name, gcs_bucket_name)

    ioloop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[
        _upload_file_to_bucket(bucket, gcs_bucket_path, fp) for fp in file_paths
    ])
    ioloop.run_until_complete(tasks)


async def _download_blob(blob: str,
                         directory: str):
    blob_base_name = blob.name.split('/')[-1]
    if blob_base_name:
        blob.download_to_filename(os.path.join(directory, blob_base_name))


def _download_blobs_from_bucket(blobs: HTTPIterator,
                                directory: str):
    ioloop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[_download_blob(blob, directory) for blob in blobs])
    ioloop.run_until_complete(tasks)


def list_bucket_contents(gcp_project_name: str,
                         gcs_bucket_name: str,
                         gcs_bucket_path: str,
                         recurse: bool=False) -> HTTPIterator:
    """List the blobs in a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_bucket_path (str): the storage path in the bucket
      recurse (bool): when True, include the contents of all subfolders (default False)
    
    Returns a google.api_core.page_iterator.HTTPIterator
    """
    bucket = get_storage_bucket(gcp_project_name, gcs_bucket_name)
    if not gcs_bucket_path.endswith('/'):
        gcs_bucket_path = gcs_bucket_path + '/'
    if recurse:
        blobs = bucket.list_blobs(prefix=gcs_bucket_path)
    else:
        blobs = bucket.list_blobs(prefix=gcs_bucket_path, delimiter='/')

    return blobs


def list_bucket_folders(gcp_project_name: str,
                        gcs_bucket_name: str,
                        gcs_bucket_path: str) -> list:
    """List the 'folders' in a Google Cloud Storage bucket path

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_bucket_path (str): the storage path in the bucket

    Returns a list of strings
    """
    folders = set()
    prefix_length = len(gcs_bucket_path.split('/'))
    for blob in list_bucket_contents(gcp_project_name,
                                     gcs_bucket_name,
                                     gcs_bucket_path,
                                     recurse=True):
        blob_path_segments = blob.name.split('/')
        if len(blob_path_segments) > prefix_length + 1:
            folders.add(blob.name.split('/')[prefix_length])

    return list(folders)


def download_file_from_gcs(gcp_project_name: str,
                           gcs_bucket_name: str,
                           gcs_file_path: str,
                           local_file_path: str) -> None:
    """Download objects from a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_file_path (str): the source object path in GCS,
                           including the file name
      local_file_path (str): the full path where the object should
                             be downloaded, including the file name
    """
    bucket = get_storage_bucket(gcp_project_name, gcs_bucket_name)
    blob = bucket.blob(gcs_file_path)
    try:
        blob.download_to_filename(local_file_path)
    except google.api_core.exceptions.NotFound:
        raise ValueError('File not found at {}'.format(gcs_file_path))


def download_files_from_gcs(gcp_project_name: str,
                            gcs_bucket_name: str,
                            gcs_bucket_path: str,
                            directory: str) -> None:
    """Download objects from a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_bucket_path (str): the storage path in the bucket
      directory (str): the full path to the local directory where the objects
                       should be downloaded
    """
    blobs = list_bucket_contents(gcp_project_name,
                                 gcs_bucket_name,
                                 gcs_bucket_path)
    _download_blobs_from_bucket(blobs, directory)


def rename_file(gcp_project_name: str,
                gcs_bucket_name: str,
                original_gcs_file_path: str,
                new_gcs_file_path: str) -> None:
    """Rename (move) an object in a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      original_gcs_file_path (str): the current full Google Cloud Storage path to
                                    the object, including the file name
      new_gcs_file_path (str): the new full Google Cloud Storage path to the object,
                               including the file name
    """
    bucket = get_storage_bucket(gcp_project_name, gcs_bucket_name)
    blob = bucket.blob(original_gcs_file_path)
    bucket.rename_blob(blob, new_gcs_file_path)


def copy_file(gcp_project_name: str,
              gcs_bucket_name: str,
              original_gcs_file_path: str,
              new_gcs_file_path: str) -> None:
    """Copy an object in a Google Cloud Storage bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      original_gcs_file_path (str): the current full Google Cloud Storage path to
                                    the object, including the file name
      new_gcs_file_path (str): the new full Google Cloud Storage path to the object,
                               including the file name
    """
    bucket = get_storage_bucket(gcp_project_name, gcs_bucket_name)
    blob = bucket.blob(original_gcs_file_path)
    bucket.copy_blob(blob, bucket, new_gcs_file_path)


def upload_file_to_gcs(gcp_project_name: str,
                       gcs_bucket_name: str,
                       gcs_bucket_path: str,
                       file_path: str) -> None:
    """Upload a single file to a Google Cloud Storage Bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_bucket_path (str): the storage path in the bucket
      file_path (str): the full path to the local directory containing the
                       file to upload
    """
    _upload_files_to_bucket(gcp_project_name,
                            gcs_bucket_name,
                            gcs_bucket_path,
                            [file_path])


def upload_files_to_gcs(gcp_project_name: str,
                        gcs_bucket_name: str,
                        gcs_bucket_path: str,
                        directory: str) -> None:
    """Upload files to a Google Cloud Storage Bucket

    Args:
      gcp_project_name (str): the Google Cloud Project name
      gcs_bucket_name (str): the Google Cloud Storage bucket name
      gcs_bucket_path (str): the storage path in the bucket
      directory (str): the full path to the local directory containing the
                       files to upload
    """
    file_paths = _get_file_paths_from_directory(directory)
    _upload_files_to_bucket(gcp_project_name,
                            gcs_bucket_name,
                            gcs_bucket_path,
                            file_paths)
