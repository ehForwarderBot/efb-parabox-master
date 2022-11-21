import copy
import pickle
import time
from abc import ABC
from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, TypeVar, Dict, Any, Optional, List, Union, Pattern

from ehforwarderbot import coordinator, Middleware
from ehforwarderbot.channel import SlaveChannel
from ehforwarderbot.chat import BaseChat, Chat, PrivateChat, ChatNotificationState, SystemChat, GroupChat
from ehforwarderbot.types import ModuleID, ChatID

from .constants import Emoji

from .utils import EFBChannelChatIDStr

if TYPE_CHECKING:
    from .db import DatabaseManager


class EPMBaseChatMixin(BaseChat, ABC):  # lgtm [py/missing-equals]
    # Allow mypy to recognize subclass output for `return self` methods.
    _Self = TypeVar('_Self', bound='EPMBaseChatMixin')
    chat_type_name = "BaseChat"

    # noinspection PyMissingConstructor
    def __init__(self, db: 'DatabaseManager', *args, **kwargs):
        self.db = db
        super().__init__(*args, **kwargs)

    def remove_from_db(self):
        """Remove this chat from database."""
        self.db.delete_slave_chat_info(self.module_id, self.uid)

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        if 'db' in state:
            del state['db']
        return state

    def __setstate__(self, state: Dict[str, Any]):
        from . import ParaboxChannel
        # Import inline to prevent cyclic import
        self.__dict__.update(state)
        with suppress(NameError, AttributeError):
            if isinstance(coordinator.master, ParaboxChannel):
                self.db = coordinator.master.db

    def __copy__(self):
        rv = self.__reduce_ex__(4)
        if isinstance(rv, str):
            return self
        obj = copy._reconstruct(self, None, *rv)
        obj.db = self.db
        return obj


class EPMChatMixin(EPMBaseChatMixin, Chat, ABC):
    _last_message_time: Optional[datetime] = None
    _last_message_time_query: float = 0
    LAST_MESSAGE_QUERY_TIMEOUT_MS: float = 60000  # 60s

    _linked: Optional[List[EFBChannelChatIDStr]] = None

    chat_type_name = "Chat"
    chat_type_emoji = Emoji.UNKNOWN

    def match(self, pattern: Union[Pattern, str, None]) -> bool:
        """
        Match the chat against a compiled regex pattern or string
        with a string in the following format::

            Channel: <Channel name>
            Name: <Chat name>
            Alias: <Chat Alias>
            ID: <Chat Unique ID>
            Type: (User|Group)
            Mode: [Linked]
            Description: <Description>
            Notification: (ALL|MENTION|NONE)
            Other: <Python Dictionary String>

        If a string is provided instead of compiled regular expression pattern,
        simple string match is used instead.

        String match is about 5x faster than re.search when there’s no
        significance of regex used.
        Ref: https://etm.1a23.studio/pull/77

        Args:
            pattern: Regex pattern or string to look for

        Returns:
            If the pattern is found in the generated string.
        """
        if pattern is None:
            return True
        mode = []
        mode_str = ', '.join(mode)
        entry_string = f"Channel: {self.module_name}\n" \
                       f"Channel ID: {self.module_id}\n" \
                       f"Name: {self.name}\n" \
                       f"Alias: {self.alias}\n" \
                       f"ID: {self.uid}\n" \
                       f"Type: {self.chat_type_name}\n" \
                       f"Mode: {mode_str}\n" \
                       f"Description: {self.description}\n" \
                       f"Notification: {self.notification.name}\n" \
                       f"Other: {self.vendor_specific}"
        if isinstance(pattern, str):
            return pattern.lower() in entry_string.lower()
        else:  # pattern is re.Pattern
            return bool(pattern.search(entry_string))

    @property
    def full_name(self) -> str:
        """Chat name with channel name and emoji"""
        chat_long_name = self.long_name
        if self.module_name:
            instance_id_idx = self.module_id.find('#')
            if instance_id_idx >= 0:
                instance_id = self.module_id[instance_id_idx + 1:]
                return f"‘{chat_long_name}’ @ ‘{self.channel_emoji} {self.module_name} ({instance_id})’"
            else:
                return f"‘{chat_long_name}’ @ ‘{self.channel_emoji} {self.module_name}’"
        else:
            return f"‘{chat_long_name}’ @ ‘{self.module_id}’"

    @property
    def chat_title(self) -> str:
        """Chat title used in updating title for Telegram group.

        Shows only alias if available.

        An asterisk (*) is added to the beginning if the channel is not
        running on its default instance.
        """
        non_default_instance_flag = "*" if "#" in self.module_id else ""
        return f"{non_default_instance_flag}" \
               f"{self.channel_emoji}{self.chat_type_emoji} " \
               f"{self.display_name}"

    def update_to_db(self):
        """Update this object to database."""
        self.db.set_slave_chat_info(self)

    @property
    def pickle(self) -> bytes:
        return pickle.dumps(self)

    def remove_from_db(self):
        super().remove_from_db()
        for i in self.members:
            self.db.delete_slave_chat_info(self.module_id, i.uid, self.uid)


class EPMPrivateChat(EPMChatMixin, PrivateChat):
    chat_type_name = "Private"
    chat_type_emoji = Emoji.USER

    def __init__(self, db: 'DatabaseManager', *, channel: Optional[SlaveChannel] = None,
                 middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, uid: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True, other_is_self: bool = False):
        super().__init__(db, channel=channel, middleware=middleware, module_name=module_name,
                         channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self,
                         other_is_self=other_is_self)


class EPMSystemChat(EPMChatMixin, SystemChat):
    chat_type_name = "System"
    chat_type_emoji = Emoji.SYSTEM

    def __init__(self, db: 'DatabaseManager', *, channel: Optional[SlaveChannel] = None,
                 middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, uid: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(db, channel=channel, middleware=middleware, module_name=module_name,
                         channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)


class EPMGroupChat(EPMChatMixin, GroupChat):
    chat_type_name = "Group"
    chat_type_emoji = Emoji.GROUP

    def __init__(self, db: 'DatabaseManager', *, channel: Optional[SlaveChannel] = None,
                 middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, uid: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(db, channel=channel, middleware=middleware, module_name=module_name,
                         channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)


EPMChatType = EPMChatMixin
EPMBaseChatType = EPMBaseChatMixin


def convert_chat(db: 'DatabaseManager', chat: Chat) -> EPMChatType:
    """Convert an EFB chat object to a EPM extended version.

    Raises:
        TypeError: if the chat type is not supported.
    """
    if isinstance(chat, EPMChatType):
        return chat
    etm_chat: EPMBaseChatType
    if isinstance(chat, PrivateChat):
        etm_chat = EPMPrivateChat(db, module_id=chat.module_id, module_name=chat.module_name,
                                  channel_emoji=chat.channel_emoji, name=chat.name, alias=chat.alias, uid=chat.uid,
                                  vendor_specific=chat.vendor_specific.copy(), description=chat.description,
                                  notification=chat.notification, with_self=chat.has_self,
                                  other_is_self=chat.other is chat.self)
        assert isinstance(etm_chat, EPMPrivateChat)  # for type check
        return etm_chat
    if isinstance(chat, SystemChat):
        etm_chat = EPMSystemChat(db, module_id=chat.module_id, module_name=chat.module_name,
                                 channel_emoji=chat.channel_emoji, name=chat.name, alias=chat.alias, uid=chat.uid,
                                 vendor_specific=chat.vendor_specific.copy(), description=chat.description,
                                 notification=chat.notification, with_self=chat.has_self)
        assert isinstance(etm_chat, EPMSystemChat)  # for type check
        return etm_chat
    if isinstance(chat, GroupChat):
        etm_chat = EPMGroupChat(db, module_id=chat.module_id, module_name=chat.module_name,
                                channel_emoji=chat.channel_emoji, name=chat.name, alias=chat.alias, uid=chat.uid,
                                vendor_specific=chat.vendor_specific.copy(), description=chat.description,
                                notification=chat.notification, with_self=False)
        assert isinstance(etm_chat, EPMGroupChat)  # for type check
        return etm_chat
    raise TypeError(f"Chat type unknown: {type(chat)}, {chat!r}")


def unpickle(data: bytes, db: 'DatabaseManager') -> EPMChatType:
    obj = pickle.loads(data)
    obj.db = db
    return obj
