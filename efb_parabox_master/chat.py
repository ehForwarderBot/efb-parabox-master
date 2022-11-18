import copy
from abc import ABC
from contextlib import suppress
from typing import TYPE_CHECKING, TypeVar, Dict, Any

from ehforwarderbot import coordinator
from ehforwarderbot.chat import BaseChat

if TYPE_CHECKING:
    from .db import DatabaseManager


class ETMBaseChatMixin(BaseChat, ABC):  # lgtm [py/missing-equals]
    # Allow mypy to recognize subclass output for `return self` methods.
    _Self = TypeVar('_Self', bound='ETMBaseChatMixin')
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
