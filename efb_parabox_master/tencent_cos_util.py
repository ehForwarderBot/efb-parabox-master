import io
import tempfile
from typing import TYPE_CHECKING

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

if TYPE_CHECKING:
    from . import ParaboxChannel


class TencentCosUtil:
    def __init__(self, channel: 'ParaboxChannel'):
        self.region = None
        self.bucket = None
        self.secret_key = None
        self.secret_id = None
        self.channel = channel
        self.config = channel.config
        self.object_storage = None

    def init(self):
        self.secret_id = self.config.get('object_storage').get('secret_id')
        self.secret_key = self.config.get('object_storage').get('secret_key')
        self.bucket = self.config.get('object_storage').get('bucket')
        self.region = self.config.get('object_storage').get('region')
        config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key, Token=None,
                           Scheme='https')
        self.object_storage = CosS3Client(config)

    def upload_file(self, file, filename):
        if self.object_storage is None:
            self.init()
        file.seek(0)
        key = 'ParaboxTemp/' + filename
        upload_response = self.object_storage.upload_file(
            Bucket=self.bucket,
            LocalFilePath=file.name,
            Key=key,
            PartSize=1,
            MAXThread=10,
            EnableMD5=False
        )
        if upload_response['ETag'] is not None:
            url_response = self.object_storage.get_presigned_download_url(Bucket=self.bucket, Key=key, Expired=3600)
            return {
                'url': url_response,
                'cloud_type': 2,
                'cloud_id': key,
            }
        else:
            return None

    def upload_bytes(self, file_bytes: io.BytesIO, filename: str):
        if self.object_storage is None:
            self.init()
        file_bytes.seek(0)
        key = 'ParaboxTemp/' + filename
        upload_response = self.object_storage.upload_file_from_buffer(
            Bucket=self.bucket,
            Body=file_bytes,
            Key=key,
            PartSize=1,
            MAXThread=10,
            EnableMD5=False
        )
        if upload_response['ETag'] is not None:
            url_response = self.object_storage.get_presigned_download_url(Bucket=self.bucket, Key=key, Expired=3600)
            return {
                'url': url_response,
                'cloud_type': 2,
                'cloud_id': key,
            }
        else:
            return None

    def download_file(self, key):
        if self.object_storage is None:
            self.init()
        download_response = self.object_storage.get_object(
            Bucket=self.bucket,
            Key=key,
        )
        return download_response['Body'].get_raw_stream().read()
