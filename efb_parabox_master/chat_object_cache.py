import logging
from typing import TYPE_CHECKING, Optional, Tuple, Dict, Iterator

from ehforwarderbot.chat import BaseChat
from ehforwarderbot.types import ModuleID, ChatID

from ehforwarderbot import coordinator, Chat
from .chat import EPMChatType, convert_chat

if TYPE_CHECKING:
    from . import ParaboxChannel

CacheKey = Tuple[ModuleID, ChatID]
"""Cache storage key: module_id, chat_id"""


class ChatObjectCacheManager:
    """Maintain and update chat objects from all slave channels and
    middlewares.
    """

    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.db = channel.db
        self.logger = logging.getLogger(__name__)

        self.cache: Dict[CacheKey, EPMChatType] = dict()

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
                self.logger.debug("Loading chat %s from '%s'...", chat, channel_id)
                # self.db.add_chat(chat)
            self.logger.debug("All %s chats from '%s' are enrolled.", len(chats), channel_id)

    def compound_enrol(self, chat: Chat) -> EPMChatType:
        """Convert and enrol a chat object for the first time.
        """
        epm_chat = convert_chat(self.db, chat)
        self.enrol(epm_chat)

        return epm_chat

    def enrol(self, chat: EPMChatType):
        """Add a chat object to the cache storage *for the first time*.

        This would not update the cached object upon conflicting.
        """
        key = self.get_cache_key(chat)
        self.cache[key] = chat
        self.logger.debug("Enrolling key %s with value %s", key, chat)

    @staticmethod
    def get_cache_key(chat: BaseChat) -> CacheKey:
        module_id = chat.module_id
        chat_id = chat.uid
        return module_id, chat_id

    def delete_chat_object(self, module_id: ModuleID, chat_id: ChatID):
        """Remove chat object from cache."""
        key = (module_id, chat_id)
        if key not in self.cache:
            return
        self.cache.pop(key)

    @property
    def all_chats(self) -> Iterator[EPMChatType]:
        """Return all chats that is not a group member and not myself."""
        return (val for val in self.cache.values() if isinstance(val, EPMChatType))
