import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParaboxChannel

from ehforwarderbot import coordinator, Chat


class ChatObjectCacheManager:
    """Maintain and update chat objects from all slave channels and
    middlewares.
    """

    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.db = channel.db
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Loading chats from slave channels...")
        # load all chats from all slave channels and convert to EPMChat object
        for channel_id, module in coordinator.slaves.items():
            # noinspection PyBroadException
            try:
                self.logger.debug("Loading chats from '%s'...", channel_id)
                chats = module.get_chats()
            except Exception:
                self.logger.exception("Error occurred while getting chats from %. "
                                      "ETM will report no chat from this channel until further noticed.", channel_id)
                continue
            self.logger.debug("Found %s chats from '%s'.", len(chats), channel_id)
            for chat in chats:
                self.logger.debug(chat)
            self.logger.debug("All %s chats from '%s' are enrolled.", len(chats), channel_id)