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
