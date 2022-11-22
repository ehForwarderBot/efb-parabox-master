# coding=utf-8
import io
import logging
import json
import time
from typing import TYPE_CHECKING

from PIL import Image
from ehforwarderbot import Message, Status, coordinator
from ehforwarderbot.chat import ChatNotificationState, SelfChatMember, GroupChat, PrivateChat, SystemChat, Chat
from ehforwarderbot.constants import MsgType
from ehforwarderbot.message import LinkAttribute, LocationAttribute, MessageCommand, Reactions, \
    StatusAttribute
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, MessageReactionsUpdate
from . import utils
from .utils import str2int

if TYPE_CHECKING:
    from . import ParaboxChannel


class SlaveMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SlaveMessageProcessor initialized.")

    def send_message(self, msg: Message) -> Message:
        # json_str = self.build_json(msg)
        # self.channel.server_manager.send_message(json_str)
        self.logger.debug(msg)
        self.logger.debug(msg.chat)
        self.logger.debug(msg.author)
        self.logger.debug(msg.attributes)
        self.logger.debug(msg.text)
        self.logger.debug(msg.commands)
        self.logger.debug(msg.deliver_to)
        self.logger.debug(msg.path)
        self.logger.debug(msg.type)
        self.logger.debug(msg.chat.uid)
        # picture = coordinator.slaves[msg.].get_chat_picture(msg.chat)
        # if not picture:
        #     return msg
        # pic_img = Image.open(picture)
        # if pic_img.size[0] < 256 or pic_img.size[1] < 256:
        #     # resize
        #     scale = 256 / min(pic_img.size)
        #     pic_resized = io.BytesIO()
        #     pic_img.resize(tuple(map(lambda a: int(scale * a), pic_img.size)), Image.BICUBIC) \
        #         .save(pic_resized, 'PNG')
        #     pic_resized.seek(0)
        # picture.seek(0)
        return msg

    def build_json(self, msg: Message) -> str:
        json_obj = {
            "contents": [],
            "profile": {
                "name": msg.author.name,
                "avatar": None,
                "id": str2int(msg.author.uid),
            },
            "subjectProfile": {
                "name": msg.chat.name,
                "avatar": None,
                "id": str2int(msg.chat.uid),
            },
            "timestamp": int(round(time.time() * 1000)),
            "messageId": str2int(msg.uid),
            "pluginConnection": {
                "connectionType": 0,
                "SendTargetType": self.get_chat_type(msg.chat),
                "id": str2int(msg.chat.uid),
            }
        }
        return json.dumps(json_obj)

    def get_chat_type(self, chat: Chat):
        if isinstance(chat, PrivateChat):
            return 0
        elif isinstance(chat, GroupChat):
            return 1
        elif isinstance(chat, SystemChat):
            return 0
        elif isinstance(chat, ChatNotificationState):
            return 0
        else:
            return 0
