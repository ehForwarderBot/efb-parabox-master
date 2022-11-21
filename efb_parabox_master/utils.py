from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParaboxChannel

EFBChannelChatIDStr = NewType('EFBChannelChatIDStr', str)
