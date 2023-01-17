# coding=utf-8
import asyncio
import base64
import io
import logging
import json
import time
from queue import Queue
from typing import TYPE_CHECKING

from PIL import Image
from ehforwarderbot import Message, Status, coordinator
from ehforwarderbot.chat import ChatNotificationState, SelfChatMember, GroupChat, PrivateChat, SystemChat, Chat
from ehforwarderbot.constants import MsgType
from ehforwarderbot.exceptions import EFBOperationNotSupported
from ehforwarderbot.message import LinkAttribute, LocationAttribute, MessageCommand, Reactions, \
    StatusAttribute
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, MessageReactionsUpdate
from . import utils

from .utils import str2int

if TYPE_CHECKING:
    from . import ParaboxChannel
    from .db import DatabaseManager


class SlaveMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.object_storage = None
        self.channel = channel
        self.config = channel.config
        self.db: 'DatabaseManager' = channel.db
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SlaveMessageProcessor initialized.")
        self.compatibility_mode = channel.config.get("compatibility_mode")
        self.msg_temp = dict()

    def send_message(self, msg: Message) -> Message:
        self.logger.info("msg_temp size: %s", len(self.msg_temp))
        if self.config.get("enable_fcm", False) is True:
            json_str = self.build_fcm_json(msg)
            self.logger.log(99, json_str)
            # self.channel.fcm_util.send(json_str)
            self.channel.xmpp_server.send(json_str)
            return msg
        else:
            json_str = self.build_json(msg)
            self.msg_temp[msg.uid] = json_str
            # self.db.set_msg_json(uid=msg.uid, json=json_str)
            self.channel.server_manager.send_message(json_str)
            return msg

    def resort_message(self, uid: str):
        try:
            self.msg_temp.pop(uid)
        except KeyError:
            pass

    def refresh_msg(self):
        for msg_json in self.msg_temp.copy().values():
            self.channel.server_manager.send_message(msg_json)

    def build_json(self, msg: Message) -> str:
        slave_msg_id = msg.uid
        slave_origin_uid = utils.chat_id_to_str(chat=msg.chat)
        channel, uid, gid = utils.chat_id_str_to_id(slave_origin_uid)

        content_obj = self.get_content_obj(msg)

        json_obj = {
            "contents": [content_obj],
            "profile": {
                "name": msg.author.name,
                "avatar": self.base64_encode(self.get_sender_avatar(msg)),
            },
            "subjectProfile": {
                "name": msg.chat.name,
                "avatar": self.base64_encode(self.get_chat_avatar(msg)),
            },
            "timestamp": int(round(time.time() * 1000)),
            "chatType": self.get_chat_type(msg.chat),
            "slaveOriginUid": slave_origin_uid,
            "slaveMsgId": slave_msg_id,
        }
        return json.dumps(json_obj)

    def base64_encode(self, file: io.BytesIO) -> str:
        file_bytes = base64.b64encode(file.read())
        return file_bytes.decode('utf-8')

    def get_chat_avatar(self, msg: Message) -> io.BytesIO:
        slave_origin_uid = utils.chat_id_to_str(chat=msg.chat)
        channel, uid, gid = utils.chat_id_str_to_id(slave_origin_uid)
        picture = coordinator.slaves[channel].get_chat_picture(msg.chat)
        if not picture:
            raise EFBOperationNotSupported()
        pic_img = Image.open(picture)

        # if pic_img.size[0] < 256 or \
        #         pic_img.size[1] < 256:
        # resize
        scale = 256 / min(pic_img.size)
        pic_resized = io.BytesIO()
        pic_img.resize(tuple(map(lambda a: int(scale * a), pic_img.size)), Image.BICUBIC) \
            .save(pic_resized, 'PNG')
        pic_resized.seek(0)
        return pic_resized
        # img_bytes = base64.b64encode(pic_resized.read())
        # return img_bytes.decode('utf-8')

    def get_sender_avatar(self, msg: Message) -> io.BytesIO:
        if self.compatibility_mode:
            return ""
        else:
            slave_origin_uid = utils.chat_id_to_str(chat=msg.chat)
            channel, uid, gid = utils.chat_id_str_to_id(slave_origin_uid)
            picture = coordinator.slaves[channel].get_chat_member_picture(msg.author)
            if not picture:
                raise EFBOperationNotSupported()
            pic_img = Image.open(picture)

            # if pic_img.size[0] < 256 or \
            #         pic_img.size[1] < 256:
            # resize
            scale = 256 / min(pic_img.size)
            pic_resized = io.BytesIO()
            pic_img.resize(tuple(map(lambda a: int(scale * a), pic_img.size)), Image.BICUBIC) \
                .save(pic_resized, 'PNG')
            pic_resized.seek(0)
            return pic_resized
            # img_bytes = base64.b64encode(pic_resized.read())
            # return img_bytes.decode('utf-8')

    def get_content_obj(self, msg: Message) -> dict:
        if msg.type == MsgType.Text:
            return self.get_text_content_obj(msg)
        elif msg.type == MsgType.Image:
            return self.get_image_content_obj(msg)
        elif msg.type == MsgType.Voice:
            return self.get_voice_content_obj(msg)
        elif msg.type == MsgType.Audio:
            return self.get_audio_content_obj(msg)
        elif msg.type == MsgType.File:
            return self.get_file_content_obj(msg)
        elif msg.type == MsgType.Animation:
            return self.get_animation_content_obj(msg)
        elif msg.type == MsgType.Video:
            return self.get_video_content_obj(msg)
        # elif msg.type == MsgType.Sticker:
        #     return self.get_sticker_content_obj(msg)
        # elif msg.type == MsgType.Location:
        #     return self.get_location_content_obj(msg)
        # elif msg.type == MsgType.Link:
        #     return self.get_link_content_obj(msg)
        # elif msg.type == MsgType.Status:
        #     return self.get_status_content_obj(msg)
        else:
            return {
                "type": 0,
                "text": msg.text,
            }

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

    def get_text_content_obj(self, msg):
        return {
            "type": 0,
            "text": msg.text,
        }

    def get_image_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        img_bytes = base64.b64encode(file.read())
        return {
            "type": 1,
            "b64String": img_bytes.decode('utf-8'),
            "fileName": msg.filename,
        }

    def get_voice_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        voice_bytes = base64.b64encode(file.read())
        return {
            "type": 2,
            "b64String": voice_bytes.decode('utf-8'),
            "fileName": msg.filename,
        }

    def get_audio_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        audio_bytes = base64.b64encode(file.read())
        return {
            "type": 3,
            "b64String": audio_bytes.decode('utf-8'),
            "fileName": msg.filename,
        }

    def get_file_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        file_bytes = base64.b64encode(file.read())
        return {
            "type": 4,
            "fileName": msg.filename,
            "b64String": file_bytes.decode('utf-8'),
        }

    def get_animation_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        file_bytes = base64.b64encode(file.read())
        return {
            "type": 5,
            "fileName": msg.filename,
            "b64String": file_bytes.decode('utf-8'),
        }

    def get_video_content_obj(self, msg):
        pass

    def get_sticker_content_obj(self, msg):
        pass

    def get_location_content_obj(self, msg):
        pass

    def get_link_content_obj(self, msg):
        pass

    def get_status_content_obj(self, msg):
        pass

    def build_fcm_json(self, msg: Message) -> str:
        slave_msg_id = msg.uid
        slave_origin_uid = utils.chat_id_to_str(chat=msg.chat)

        content_obj = self.get_fcm_content_obj(msg)

        chat_avatar = self.upload_bytes(self.get_chat_avatar(msg), msg.chat.name + ".png")
        sender_avatar = self.upload_bytes(self.get_sender_avatar(msg), msg.author.name + ".png")
        json_obj = {
            "contents": [content_obj],
            "profile": {
                "name": msg.author.name,
                "avatar": sender_avatar.get("url"),
                "avatar_cloud_type": sender_avatar.get("cloud_type"),
                "avatar_cloud_id": sender_avatar.get("cloud_id")
            },
            "subjectProfile": {
                "name": msg.chat.name,
                "avatar": chat_avatar.get("url"),
                "avatar_cloud_type": chat_avatar.get("cloud_type"),
                "avatar_cloud_id": chat_avatar.get("cloud_id")
            },
            "timestamp": int(round(time.time() * 1000)),
            "chatType": self.get_chat_type(msg.chat),
            "slaveOriginUid": slave_origin_uid,
            "slaveMsgId": slave_msg_id,
        }
        return json.dumps(json_obj)

    def get_fcm_content_obj(self, msg):
        if msg.type == MsgType.Text:
            return self.get_text_content_obj(msg)
        elif msg.type == MsgType.Image:
            return self.get_fcm_image_content_obj(msg)
        # elif msg.type == MsgType.Voice:
        #     return self.get_fcm_voice_content_obj(msg)
        # elif msg.type == MsgType.Audio:
        #     return self.get_fcm_audio_content_obj(msg)
        # elif msg.type == MsgType.File:
        #     return self.get_fcm_file_content_obj(msg)
        # elif msg.type == MsgType.Animation:
        #     return self.get_fcm_animation_content_obj(msg)
        # elif msg.type == MsgType.Video:
        #     return self.get_fcm_video_content_obj(msg)
        # elif msg.type == MsgType.Sticker:
        #     return self.get_fcm_sticker_content_obj(msg)
        # elif msg.type == MsgType.Location:
        #     return self.get_fcm_location_content_obj(msg)
        # elif msg.type == MsgType.Link:
        #     return self.get_fcm_link_content_obj(msg)
        # elif msg.type == MsgType.Status:
        #     return self.get_fcm_status_content_obj(msg)
        else:
            return {
                "type": 0,
                "text": msg.text,
            }

    def get_fcm_image_content_obj(self, msg):
        file = msg.file
        file.seek(0)
        res = self.upload_file(file, msg.filename)
        self.logger.log(99, res)
        if res is not None:
            return {
                "type": 1,
                "url": res.get('url'),
                "cloud_type": res.get('cloud_type'),
                "cloud_id": res.get('cloud_id'),
                "file_mame": msg.filename,
            }
        else:
            return {
                "type": 1,
                "url": '',
                "cloud_type": '',
                "cloud_id": '',
                "file_name": msg.filename,
            }

    def get_fcm_voice_content_obj(self, msg):
        pass

    def get_fcm_audio_content_obj(self, msg):
        pass

    def get_fcm_file_content_obj(self, msg):
        pass

    def get_fcm_animation_content_obj(self, msg):
        pass

    def get_fcm_video_content_obj(self, msg):
        pass

    def upload_file(self, file, filename):
        if self.config.get('object_storage') is None:
            return None
        else:
            if self.config.get('object_storage').get('type') == 'qiniu':
                return self.channel.qiniu_util.upload_file(file, filename)
            elif self.config.get('object_storage').get('type') == 'tencent_cos':
                return self.channel.tencent_cos_util.upload_file(file, filename)
            else:
                return None

    def upload_bytes(self, file_bytes, filename):
        if self.config.get('object_storage') is None:
            return None
        else:
            if self.config.get('object_storage').get('type') == 'qiniu':
                return self.channel.qiniu_util.upload_bytes(file_bytes, filename)
            elif self.config.get('object_storage').get('type') == 'tencent_cos':
                return self.channel.tencent_cos_util.upload_bytes(file_bytes, filename)
            else:
                return None

