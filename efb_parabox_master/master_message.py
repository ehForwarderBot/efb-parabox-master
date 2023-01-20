
import base64
import json
import logging
import tempfile
from typing import TYPE_CHECKING

from ehforwarderbot import coordinator
from ehforwarderbot import utils as efb_utils
from ehforwarderbot.chat import SelfChatMember
from ehforwarderbot.constants import MsgType
from ehforwarderbot.exceptions import EFBMessageTypeNotSupported, EFBChatNotFound, \
    EFBOperationNotSupported, EFBException
from ehforwarderbot.types import MessageID

from . import utils, ChatObjectCacheManager
from .message import EPMMsg

if TYPE_CHECKING:
    from . import ParaboxChannel
    from .db import DatabaseManager


class MasterMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.db: 'DatabaseManager' = channel.db
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MasterMessageProcessor initialized.")
        self.chat_manager: ChatObjectCacheManager = channel.chat_manager

    def process_parabox_message(self, json_obj):
        """
        Process a message received from Parabox.
        """
        if json_obj['type'] == 'message':
            self.logger.info("Processing message from Parabox.")
            self.process_parabox_message_message(json_obj['data'])
        elif json_obj['type'] == 'recall':
            self.logger.info("Processing message recall from Parabox.")
            self.process_parabox_message_recall(json_obj['data'])
        elif json_obj['type'] == 'response':
            self.logger.info("Processing response from Parabox.")
            # self.db.resort_msg_json(json_obj['data'])
            self.channel.slave_messages.resort_message(json_obj['data'])
        elif json_obj['type'] == 'refresh':
            self.logger.info("Processing refresh from Parabox.")
            self.channel.slave_messages.refresh_msg()
            # self.channel.server_manager.send_all_failed_msg()
        elif json_obj['type'] == 'server':
            self.logger.info("Processing message from FCM.")
            self.process_parabox_server_message(json.loads(json_obj['data']))
        else:
            self.logger.warning("Unknown message type: %s", json_obj['type'])

    def process_parabox_message_message(self, param):
        data_path = efb_utils.get_data_path(self.channel.channel_id)
        destination = param['slaveOriginUid']
        mtype = param['content']['type']
        channel, uid, gid = utils.chat_id_str_to_id(destination)
        if channel not in coordinator.slaves:
            return
        m = EPMMsg()
        try:
            m.type = get_msg_type(mtype)
            self.logger.debug("[%s] EFB message type: %s", m.uid, m.type)
            # Chat and author related stuff
            m.chat = self.chat_manager.get_chat(channel, uid, build_dummy=True)
            if m.chat.has_self:
                m_author = SelfChatMember(m.chat)
            else:
                m_author = m.chat.add_self()
            m.author = m_author

            m.deliver_to = coordinator.slaves[channel]

            if m.type not in coordinator.slaves[channel].supported_message_types:
                self.logger.info("[%s] Message type %s is not supported by channel %s",
                                 m.uid, m.type.name, channel)
                raise EFBMessageTypeNotSupported(
                    "{type_name} messages are not supported by slave channel {channel_name}.")

            if mtype == 0:
                m.text = param['content']['text']
            elif mtype == 1:
                file_name = param['content']['fileName']
                f = tempfile.NamedTemporaryFile(suffix=".jpg")
                f.write(base64.b64decode(param['content']['b64String']))
                f.seek(0)
                m.file = f
                m.filename = file_name
                m.mime = "image/jpeg"
            elif mtype == 2:
                file_name = param['content']['fileName']
                f = tempfile.NamedTemporaryFile(suffix=".mp3")
                f.write(base64.b64decode(param['content']['b64String']))
                f.seek(0)
                m.file = f
                m.filename = file_name
                m.mime = "audio/mpeg"
            elif mtype == 3:
                file_name = param['content']['fileName']
                f = tempfile.NamedTemporaryFile(suffix=".mpeg")
                f.write(base64.b64decode(param['content']['b64String']))
                f.seek(0)
                m.file = f
                m.filename = file_name
                m.mime = "video/mpeg"
            elif mtype == 4:
                file_name = param['content']['fileName']
                f = tempfile.NamedTemporaryFile()
                f.name = file_name
                f.write(base64.b64decode(param['content']['b64String']))
                f.seek(0)
                m.file = f
                m.filename = file_name
                m.mime = "application/octet-stream"

            elif mtype == 5:
                file_name = param['content']['fileName']
                f = tempfile.NamedTemporaryFile(suffix=".gif")
                f.write(base64.b64decode(param['content']['b64String']))
                f.seek(0)
                m.file = f
                m.filename = file_name
                m.mime = "image/gif"

            slave_msg = coordinator.send_message(m)
            if slave_msg and slave_msg.uid:
                m.uid = slave_msg.uid
            else:
                m.uid = None
        except EFBChatNotFound as e:
            self.logger.exception("Chat is not found.. (exception: %s)", e)
        except EFBMessageTypeNotSupported as e:
            self.logger.exception("Message type is not supported... (exception: %s)", e)
        except EFBOperationNotSupported as e:
            self.logger.exception("Message editing is not supported.. (exception: %s)", e)
        except EFBException as e:
            self.logger.exception("Message is not sent. (exception: %s)", e)
        except Exception as e:
            self.logger.exception("Message is not sent. (exception: %s)", e)
        finally:
            pass

    def process_parabox_message_recall(self, param):
        pass

    def process_parabox_server_message(self, param):
        data_path = efb_utils.get_data_path(self.channel.channel_id)
        destination = param['slaveOriginUid']
        channel, uid, gid = utils.chat_id_str_to_id(destination)
        if channel not in coordinator.slaves:
            return
        try:
            for content in param['contents']:
                mtype = content['type']
                m = EPMMsg()
                m.type = get_msg_type(mtype)
                self.logger.debug("[%s] EFB message type: %s", m.uid, m.type)
                # Chat and author related stuff
                m.chat = self.chat_manager.get_chat(channel, uid, build_dummy=True)
                if m.chat.has_self:
                    m_author = SelfChatMember(m.chat)
                else:
                    m_author = m.chat.add_self()
                m.author = m_author

                m.deliver_to = coordinator.slaves[channel]

                if m.type not in coordinator.slaves[channel].supported_message_types:
                    self.logger.info("[%s] Message type %s is not supported by channel %s",
                                     m.uid, m.type.name, channel)
                    raise EFBMessageTypeNotSupported(
                        "{type_name} messages are not supported by slave channel {channel_name}.")

                if mtype == 0:
                    m.text = content['text']
                elif mtype == 1:
                    file_name = content['file_name']
                    f = tempfile.NamedTemporaryFile(suffix=".jpg")
                    f.write(self.download_file(content['cloud_type'], content['cloud_id']))
                    f.seek(0)
                    m.file = f
                    m.filename = file_name
                    m.mime = "image/jpeg"
                elif mtype == 2:
                    file_name = content['file_name']
                    f = tempfile.NamedTemporaryFile(suffix=".mp3")
                    f.write(self.download_file(content['cloud_type'], content['cloud_id']))
                    f.seek(0)
                    m.file = f
                    m.filename = file_name
                    m.mime = "audio/mpeg"
                elif mtype == 3:
                    file_name = content['file_name']
                    f = tempfile.NamedTemporaryFile(suffix=".mpeg")
                    f.write(self.download_file(content['cloud_type'], content['cloud_id']))
                    f.seek(0)
                    m.file = f
                    m.filename = file_name
                    m.mime = "video/mpeg"
                elif mtype == 4:
                    file_name = content['file_name']
                    f = tempfile.NamedTemporaryFile()
                    f.name = file_name
                    f.write(self.download_file(content['cloud_type'], content['cloud_id']))
                    f.seek(0)
                    m.file = f
                    m.filename = file_name
                    m.mime = "application/octet-stream"

                elif mtype == 5:
                    file_name = content['fileName']
                    f = tempfile.NamedTemporaryFile(suffix=".gif")
                    f.write(self.download_file(content['cloud_type'], content['cloud_id']))
                    f.seek(0)
                    m.file = f
                    m.filename = file_name
                    m.mime = "image/gif"

                slave_msg = coordinator.send_message(m)
                if slave_msg and slave_msg.uid:
                    m.uid = slave_msg.uid
                else:
                    m.uid = None
        except EFBChatNotFound as e:
            self.logger.exception("Chat is not found.. (exception: %s)", e)
        except EFBMessageTypeNotSupported as e:
            self.logger.exception("Message type is not supported... (exception: %s)", e)
        except EFBOperationNotSupported as e:
            self.logger.exception("Message editing is not supported.. (exception: %s)", e)
        except EFBException as e:
            self.logger.exception("Message is not sent. (exception: %s)", e)
        except Exception as e:
            self.logger.exception("Message is not sent. (exception: %s)", e)
        finally:
            pass

    def download_file(self, cloud_type, cloud_id):
        if cloud_type == 2:
            return self.channel.tencent_cos_util.download_file(cloud_id)
        elif cloud_type == 3:
            return self.channel.qiniu_util.download_file(cloud_id)

def get_msg_type(msg_type: int) -> MsgType:
    if msg_type == 0:
        return MsgType.Text
    elif msg_type == 1:
        return MsgType.Image
    elif msg_type == 2:
        return MsgType.Voice
    elif msg_type == 3:
        return MsgType.Audio
    elif msg_type == 4:
        return MsgType.File
    elif msg_type == 5:
        return MsgType.Animation
    else:
        raise EFBMessageTypeNotSupported()
