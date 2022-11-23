from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParaboxChannel

EFBChannelChatIDStr = NewType('EFBChannelChatIDStr', str)


def str2int(s: str) -> int:
    r = ''
    for i in s:
        if i.isdigit():
            r += i
    return int(r)


def get_chat_id(dto) -> str:
    target_type = dto['pluginConnection']['sendTargetType']
    if target_type == 0:
        return f"friend_${dto['pluginConnection']['id']}"
    elif target_type == 1:
        return f"group_${dto['pluginConnection']['id']}"
    else:
        return f"unknown_${dto['pluginConnection']['id']}"
