# coding=utf-8

import logging
import mimetypes
import time
from abc import ABC
from typing import Optional

import ehforwarderbot  # lgtm [py/import-and-import-from]
from PIL import Image, WebPImagePlugin
from ehforwarderbot import Channel, coordinator
from ehforwarderbot import utils as efb_utils
from ehforwarderbot.channel import MasterChannel
from ehforwarderbot.message import Message as EFBMessage, Message
from ehforwarderbot.chat import Chat
from ehforwarderbot.status import Status
from ehforwarderbot.constants import MsgType
from ehforwarderbot.exceptions import EFBException, EFBOperationNotSupported, EFBChatNotFound, \
    EFBMessageReactionNotPossible
from ehforwarderbot.status import ReactToMessage
from ehforwarderbot.types import ModuleID, InstanceID, MessageID, ReactionName, ChatID
from ruamel.yaml import YAML

from .chat_object_cache import ChatObjectCacheManager
from .db import DatabaseManager
from .fcm_client import FcmClient
from .master_message import MasterMessageProcessor
from .qiniu_util import QiniuUtil
from .server import ServerManager
from .slave_message import SlaveMessageProcessor
from . import utils as epm_utils
from .__version__ import __version__
from .tencent_cos_util import TencentCosUtil


class ParaboxChannel(MasterChannel):
    # Meta Info
    channel_name = "Parabox Master"
    channel_emoji = "📦"
    channel_id = ModuleID("ojhdt.parabox")
    supported_message_types = [MsgType.Text]

    __version__ = __version__

    # Data
    _stop_polling = False
    timeout_count = 0
    last_poll_confliction_time = 0.0
    CONFLICTION_TIMEOUT = 60

    # Constants
    config: dict

    def __init__(self, instance_id: InstanceID = None):
        super().__init__(instance_id)

        # Check PIL support for WebP
        Image.init()
        if 'WEBP' not in Image.ID or not getattr(WebPImagePlugin, "SUPPORTED", None):
            raise EFBException(self._("WebP support of Pillow is required.\n"
                                      "Please refer to Pillow Documentation for instructions.\n"
                                      "https://pillow.readthedocs.io/"))

        # Set up logger
        self.logger: logging.Logger = logging.getLogger(__name__)
        logger = logging.getLogger('peewee')
        logger.setLevel(logging.WARNING)

        # Load configs
        self.load_config()

        # Initialize managers
        self.db: DatabaseManager = DatabaseManager(self)
        self.chat_manager: ChatObjectCacheManager = ChatObjectCacheManager(self)
        self.slave_messages: SlaveMessageProcessor = SlaveMessageProcessor(self)
        self.master_messages: MasterMessageProcessor = MasterMessageProcessor(self)
        self.tencent_cos_util: TencentCosUtil = TencentCosUtil(self)
        self.qiniu_util: QiniuUtil = QiniuUtil(self)

        if self.config.get("enable_fcm", False) is True:
            self.fcm_client: FcmClient = FcmClient(self)
        else:
            self.server_manager: ServerManager = ServerManager(self)
        # Load predefined MIME types
        mimetypes.init(files=["mimetypes"])

    def load_config(self):
        config_path = efb_utils.get_config_path(self.channel_id)
        if not config_path.exists():
            raise FileNotFoundError("Config File does not exist. ({path})")
        with config_path.open() as f:
            data = YAML().load(f)

            # Verify configuration
            if not isinstance(data.get('host', None), str):
                raise ValueError('Websocket server host must be a string')
            if not isinstance(data.get('port', None), int):
                raise ValueError('Websocket server port must be a number')
            if not isinstance(data.get('token', None), str):
                raise ValueError('Websocket server token must be a string')
            self.config = data.copy()

    def send_message(self, msg: EFBMessage) -> EFBMessage:
        return self.slave_messages.send_message(msg)

    def poll(self):
        """
        Message polling process.
        """
        if self.config.get("enable_fcm", False) is True:
            pass
        else:
            self.server_manager.pulling()

    def send_status(self, status: 'Status'):
        if self.config.get("enable_fcm", False) is True:
            pass
        else:
            self.server_manager.send_status(status)

    def stop_polling(self):
        self.logger.debug("Gracefully stopping %s (%s).", self.channel_name, self.channel_id)
        if self.config.get("enable_fcm", False) is True:
            pass
        else:
            self.server_manager.graceful_stop()