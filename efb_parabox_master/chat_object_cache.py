import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Optional, Tuple, Dict, Iterator, overload, Literal

from ehforwarderbot.chat import BaseChat
from ehforwarderbot.exceptions import EFBChatNotFound
from ehforwarderbot.types import ModuleID, ChatID

from ehforwarderbot import coordinator, Chat
from .chat import EPMChatType, convert_chat, unpickle, EPMSystemChat

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
                self.compound_enrol(chat, channel_id)
            self.logger.debug("All %s chats from '%s' are enrolled.", len(chats), channel_id)

    def compound_enrol(self, chat: Chat, channel_id: str) -> EPMChatType:
        """Convert and enrol a chat object for the first time.
        """
        epm_chat = convert_chat(self.db, chat, channel_id)
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

    @overload
    def get_chat(self, module_id: ModuleID, chat_id: ChatID, build_dummy: Literal[True]) -> EPMChatType:
        ...

    @overload
    def get_chat(self, module_id: ModuleID, chat_id: ChatID, build_dummy: bool = False) -> Optional[EPMChatType]:
        ...

    def get_chat(self, module_id: ModuleID, chat_id: ChatID, build_dummy: bool = False) -> Optional[EPMChatType]:
        """
        Get an ETMChat object of a chat from cache.

        If the object queried is not found, try to get from database cache,
        then the relevant channel. If still not found, return None.

        If build_dummy is set to True, this will return a dummy object with
        the module_id, chat_id and group_id specified.
        """
        key = (module_id, chat_id)
        if key in self.cache:
            return self.cache[key]

        c_log = self.db.get_slave_chat_info(module_id, chat_id)
        if c_log is not None and c_log.pickle:
            # Suppress AttributeError caused by change of class name in EFB 2.0.0b26, ETM 2.0.0b40
            with suppress(AttributeError):
                obj = unpickle(c_log.pickle, self.db)
                self.enrol(obj)
                return obj

        # Only look up from slave channels as middlewares don’t have get_chat_by_id method.
        if module_id in coordinator.slaves:
            with suppress(EFBChatNotFound, KeyError):
                chat_obj = coordinator.slaves[module_id].get_chat(chat_id)
                return self.compound_enrol(chat_obj)

        if build_dummy:
            return EPMSystemChat(self.db,
                                 module_id=module_id,
                                 module_name=module_id,
                                 uid=chat_id,
                                 name=chat_id)
        return None

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
