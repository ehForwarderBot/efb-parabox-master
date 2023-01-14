from typing import TYPE_CHECKING
from qiniu import Auth, put_file, etag, BucketManager
import qiniu.config

if TYPE_CHECKING:
    from . import ParaboxChannel


class QiniuUtil:
    def __init__(self, channel: 'ParaboxChannel'):
        self.domain = None
        self.bucket = None
        self.secret_key = None
        self.access_key = None
        self.channel = channel
        self.config = channel.config

    def init(self):
        self.access_key = self.config.get('object_storage').get('access_key')
        self.secret_key = self.config.get('object_storage').get('secret_key')
        self.bucket = self.config.get('object_storage').get('bucket')
        self.domain = self.config.get('object_storage').get('domain')

    def upload_file(self, file, filename):
        file.seek(0)
        self.init()

        q = Auth(self.access_key, self.secret_key)
        key = 'ParaboxTemp/' + filename
        token = q.upload_token(self.bucket, key, 3600)
        ret, info = put_file(token, key, file.name)
        if ret['key'] is not None:
            return {
                'url': self.domain + ret['key'],
                'cloud_type': 3,
                'cloud_id': ret['key'],
            }
        else:
            return None

    def download_file(self, key):
        self.init()

        q = Auth(self.access_key, self.secret_key)
        bucket = BucketManager(q)
        ret, info = bucket.fetch(self.domain + key, self.bucket, key)
        return ret['data']