from typing import TYPE_CHECKING
import firebase_admin
from firebase_admin import credentials, messaging
from ehforwarderbot import utils as efb_utils

if TYPE_CHECKING:
    from . import ParaboxChannel


class FCMUtil:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.config = channel.config
        self.logger = channel.logger
        self.fcm_token = self.config.get('fcm_token')
        self.authorization_file_path = self.config.get('authorization_file_path')
        self.app = None

    def init(self):
        path = efb_utils.get_data_path(self.channel.channel_id) / self.authorization_file_path
        cred = credentials.Certificate(path)
        self.app = firebase_admin.initialize_app(credential=cred)

    def send(self, data: str):
        if self.app is None:
            self.init()
        message = messaging.Message(
            data=data,
            token=self.fcm_token,
        )
        response = messaging.send(message)
        self.logger.log(99, 'Successfully sent message: %s', response)
