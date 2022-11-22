from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParaboxChannel

EFBChannelChatIDStr = NewType('EFBChannelChatIDStr', str)


# 将一串字母映射为依次连接的数字
def str2int(s: str) -> int:
    return int(''.join(map(lambda c: str(ord(c)), s)))
