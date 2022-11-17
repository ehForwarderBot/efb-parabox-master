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


class DatabaseManager:
    logger = logging.getLogger(__name__)
    FAIL_FLAG = '__fail__'

    def __init__(self, channel: 'ParaboxChannel'):
        base_path = utils.get_data_path(channel.channel_id)

        self.logger.debug("Loading database...")
        database.init(str(base_path / 'pbdata.db'))
        database.start()
        database.connect()
        self.logger.debug("Database loaded.")