from typing import NewType, TYPE_CHECKING, Optional, Tuple

from ehforwarderbot import Channel
from ehforwarderbot.chat import BaseChat, ChatMember
from ehforwarderbot.types import ModuleID, ChatID

if TYPE_CHECKING:
    from . import ParaboxChannel

EFBChannelChatIDStr = NewType('EFBChannelChatIDStr', str)


def chat_id_to_str(channel_id: Optional[ModuleID] = None, chat_uid: Optional[ChatID] = None,
                   group_id: Optional[ChatID] = None,
                   chat: Optional[BaseChat] = None, channel: Optional[Channel] = None) -> EFBChannelChatIDStr:
    """
    Convert an unique identifier to EFB chat to a string.

    (chat|((channel|channel_id), chat_uid)) must be provided.

    Returns:
        String representation of the chat
    """

    if not chat and not chat_uid:
        raise ValueError("Either chat or the other set must be provided.")
    if chat and chat_uid:
        raise ValueError("Either chat or the other set must be provided, but not both.")
    if chat_uid and channel_id and channel:
        raise ValueError("channel_id and channel is mutual exclusive.")

    if chat:
        channel_id = chat.module_id
        chat_uid = chat.uid
        if isinstance(chat, ChatMember):
            group_id = chat.chat.uid
    if channel:
        channel_id = channel.channel_id
    if group_id is None:
        return EFBChannelChatIDStr(f"{channel_id} {chat_uid}")

    return EFBChannelChatIDStr(f"{channel_id} {chat_uid} {group_id}")


def chat_id_str_to_id(s: EFBChannelChatIDStr) -> Tuple[ModuleID, ChatID, Optional[ChatID]]:
    """
    Reverse of chat_id_to_str.
    Returns:
        channel_id, chat_uid, group_id
    """
    ids = s.split(" ", 2)
    channel_id = ModuleID(ids[0])
    chat_uid = ChatID(ids[1])
    if len(ids) < 3:
        group_id = None
    else:
        group_id = ChatID(ids[2])
    return channel_id, chat_uid, group_id


def str2int(s: str) -> int:
    r = ''
    for i in s:
        if i.isdigit():
            r += i
    return int(r)


def get_chat_id(dto) -> str:
    target_type = dto['pluginConnection']['sendTargetType']
    if target_type == 0:
        return f"friend_{dto['pluginConnection']['id']}"
    elif target_type == 1:
        return f"group_{dto['pluginConnection']['id']}"
    else:
        return f"unknown_{dto['pluginConnection']['id']}"
