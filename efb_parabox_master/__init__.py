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

from .server import ServerManager
from .slave_message import SlaveMessageProcessor
from . import utils as epm_utils
from .__version__ import __version__


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
        self.slave_messages = None
        Image.init()
        if 'WEBP' not in Image.ID or not getattr(WebPImagePlugin, "SUPPORTED", None):
            raise EFBException(self._("WebP support of Pillow is required.\n"
                                      "Please refer to Pillow Documentation for instructions.\n"
                                      "https://pillow.readthedocs.io/"))

        # Set up logger
        self.logger: logging.Logger = logging.getLogger(__name__)

        # Load configs
        self.load_config()

        # Initialize managers
        self.slave_messages: SlaveMessageProcessor = SlaveMessageProcessor(self)
        self.master_messages: MasterMessageProcessor = MasterMessageProcessor(self)
        self.server_manager: ServerManager = ServerManager(self)

        # Load predefined MIME types
        mimetypes.init(files=["mimetypes"])

    def load_config(self):
        config_path = efb_utils.get_config_path(self.channel_id)
        if not config_path.exists():
            raise FileNotFoundError(self._("Config File does not exist. ({path})").format(path=config_path))
        with config_path.open() as f:
            data = YAML().load(f)

            self.config = data.copy()

    def send_message(self, msg: EFBMessage) -> EFBMessage:
        return self.slave_messages.send_message(msg)

    def poll(self):
        """
        Message polling process.
        """
        self.server_manager.pulling()

    def send_status(self, status: 'Status'):
        pass

    def stop_polling(self):
        self.logger.debug("Gracefully stopping %s (%s).", self.channel_name, self.channel_id)
        self.server_manager.graceful_stop()
        pass

    def get_message_by_id(self, chat: Chat,
                          msg_id: MessageID) -> Optional[EFBMessage]:
        pass
