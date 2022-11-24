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
from . import utils, ChatObjectCacheManager
from .message import EPMMsg
from .utils import get_chat_id

if TYPE_CHECKING:
    from . import ParaboxChannel


class MasterMessageProcessor:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MasterMessageProcessor initialized.")
        self.chat_manager: ChatObjectCacheManager = channel.chat_manager

    def process_parabox_message(self, json_obj):
        """
        Process a message received from Parabox.
        """
        self.logger.debug(json_obj)
        if json_obj['type'] == 'message':
            self.process_parabox_message_message(json_obj['data'])
        elif json_obj['type'] == 'recall':
            self.process_parabox_message_recall(json_obj['data'])
        else:
            self.logger.warning("Unknown message type: %s", json_obj['type'])

    def process_parabox_message_message(self, param):
        destination = param['slaveOriginUid']
        msg_id = param["slaveMsgId"]
        mtype = param['content']['type']
        channel, uid, gid = utils.chat_id_str_to_id(destination)
        if channel not in coordinator.slaves:
            return
        m = EPMMsg()
        try:
            m.uid = MessageID(msg_id)
            m.type = get_msg_type(mtype)
            self.logger.debug("[%s] EFB message type: %s", m.uid, m.type)
            # Chat and author related stuff
            m.chat = self.chat_manager.get_chat(channel, uid, build_dummy=True)
            m.author = m.chat.self or m.chat.add_self()

            m.deliver_to = coordinator.slaves[channel]

            if m.type not in coordinator.slaves[channel].supported_message_types:
                self.logger.info("[%s] Message type %s is not supported by channel %s",
                                 m.uid, m.type.name, channel)
                raise EFBMessageTypeNotSupported(
                    "{type_name} messages are not supported by slave channel {channel_name}.")

            if mtype == 0:
                m.text = param['content']['text']

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


def get_msg_type(msg_type: int) -> MsgType:
    if msg_type == 0:
        return MsgType.Text
    elif msg_type == 1:
        return MsgType.Image
    elif msg_type == 2:
        return MsgType.Text
    elif msg_type == 3:
        return MsgType.Audio
    elif msg_type == 4:
        return MsgType.Text
    elif msg_type == 5:
        return MsgType.Text
    elif msg_type == 6:
        return MsgType.File
    else:
        raise EFBMessageTypeNotSupported()
