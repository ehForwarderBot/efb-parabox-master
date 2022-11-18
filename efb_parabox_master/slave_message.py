# coding=utf-8

import logging
from typing import TYPE_CHECKING

from ehforwarderbot import Message, Status, coordinator
from ehforwarderbot.chat import ChatNotificationState, SelfChatMember, GroupChat, PrivateChat, SystemChat, Chat
from ehforwarderbot.constants import MsgType
from ehforwarderbot.message import LinkAttribute, LocationAttribute, MessageCommand, Reactions, \
    StatusAttribute
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, MessageReactionsUpdate
from . import utils

if TYPE_CHECKING:
    from . import ParaboxChannel


class SlaveMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SlaveMessageProcessor initialized.")

    def send_message(self, msg: Message) -> Message:
        self.logger.debug(msg.chat)
        self.logger.debug(msg.author)
        self.logger.debug(msg.attributes)
        self.logger.debug(msg.text)
        self.logger.debug(msg.commands)
        self.logger.debug(msg.deliver_to)
        self.logger.debug(msg.path)
        self.logger.debug(msg.type)
        self.logger.debug(msg.vendor_specific)
        return msg
