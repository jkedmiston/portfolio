import os
import json
import datetime
from google.cloud import storage
from google.oauth2 import service_account


def get_signed_url_from_blob(blob):
    """
    Ref: https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers#code-samples
    """
    url = blob.generate_signed_url(
        version='v4', expiration=datetime.timedelta(minutes=15), method='GET')
    return url


def upload_file(filename):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    """
    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    project_id = service_account_info["project_id"]
    bucket_name = os.environ["STORAGE_BUCKET"]
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    storage_client = storage.Client(
        project=project_id, credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(os.path.basename(filename))
    blob.upload_from_filename(filename)
    print(
        "File {} uploaded to {}.".format(
            filename, filename
        )
    )
    return blob
