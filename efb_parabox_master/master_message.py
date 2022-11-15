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

if TYPE_CHECKING:
    from . import ParaboxChannel


class MasterMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.logger = logging.getLogger(__name__)

    def send_message(self, msg: Message) -> Message:
        pass
