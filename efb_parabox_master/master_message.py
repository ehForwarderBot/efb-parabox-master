import logging
from queue import Queue
from threading import Thread
from typing import Optional, TYPE_CHECKING, Tuple, Any

from ehforwarderbot import coordinator
from ehforwarderbot.constants import MsgType
from ehforwarderbot.exceptions import EFBMessageTypeNotSupported, EFBChatNotFound, \
    EFBMessageError, EFBOperationNotSupported, EFBException
from ehforwarderbot.message import LocationAttribute, Message
from ehforwarderbot.status import MessageRemoval
from ehforwarderbot.types import ModuleID, MessageID, ChatID
from . import utils
from .message import EPMMsg
from .utils import get_chat_id

if TYPE_CHECKING:
    from . import ParaboxChannel


class MasterMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MasterMessageProcessor initialized.")

    def process_parabox_message(self, json_obj):
        """
        Process a message received from Parabox.
        """
        self.logger.debug(json_obj)
        if json_obj['type'] == 'message':
            self.process_parabox_message_message(json_obj["data"])
        elif json_obj['type'] == 'recall':
            self.process_parabox_message_recall(json_obj["data"])
        else:
            self.logger.warning("Unknown message type: %s", json_obj['type'])

    def process_parabox_message_message(self, param):
        chat_id = get_chat_id(param)
        self.logger.debug("Chat ID: %s", chat_id)
        chat = self.channel.chat_manager.get_chat(chat_id)
        self.logger.debug("Chat: %s", chat)
        self.logger.debug("module Id: %s", chat.module_id)

        m = EPMMsg()

    def process_parabox_message_recall(self, param):
        pass
