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

    def send_message(self, msg: Message) -> Message:
        print(msg)
        return msg
