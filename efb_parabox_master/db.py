# coding=utf-8

import logging
from typing import TYPE_CHECKING

from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.migrate import SqliteMigrator, migrate

from ehforwarderbot import Message as EFBMessage
from ehforwarderbot import utils, Channel, coordinator, MsgType
from ehforwarderbot.message import Substitutions, MessageCommands, MessageAttribute
from ehforwarderbot.types import ModuleID, ChatID, MessageID, ReactionName

if TYPE_CHECKING:
    from . import ParaboxChannel

database = SqliteQueueDatabase(None, autostart=False)