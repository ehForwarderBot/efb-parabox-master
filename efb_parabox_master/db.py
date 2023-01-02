# coding=utf-8

import logging
import time
from typing import TYPE_CHECKING, Optional, Dict

from ehforwarderbot import utils
from ehforwarderbot.types import ModuleID, ChatID
from peewee import TextField, CharField, BlobField, Model, DoesNotExist, IntegerField, TimestampField
from playhouse.migrate import SqliteMigrator, migrate
from playhouse.sqliteq import SqliteQueueDatabase

if TYPE_CHECKING:
    from . import ParaboxChannel

database = SqliteQueueDatabase(None, autostart=False)


class BaseModel(Model):
    class Meta:
        database = database


class SlaveChatInfo(BaseModel):
    slave_channel_id = TextField()
    slave_channel_emoji = CharField()
    slave_chat_uid = TextField()
    slave_chat_group_id = TextField(null=True)
    slave_chat_name = TextField()
    slave_chat_alias = TextField(null=True)
    slave_chat_type = CharField()
    pickle = BlobField(null=True)


class MsgJson(BaseModel):
    uid = TextField(unique=True, primary_key=True)
    json = TextField()
    tried = IntegerField()
    last_try_timestamp = TimestampField(default=0)


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

        self.logger.debug("Checking database migration...")
        if not MsgJson.table_exists():
            self._create()
        else:
            msg_json_columns = {i.name for i in database.get_columns("msgjson")}
            slave_chat_info_columns = {i.name for i in database.get_columns("slavechatinfo")}
            if "last_try_timestamp" not in msg_json_columns:
                self._migrate(0)

    def stop_worker(self):
        database.stop()

    @staticmethod
    def _create():
        """
        Initializing tables.
        """
        database.create_tables([SlaveChatInfo, MsgJson])

    @staticmethod
    def _migrate(i: int):
        """
        Run migrations.

        Args:
            i: Migration ID
        """
        migrator = SqliteMigrator(database)

        if i <= 0:
            # Migration 0: Add media file ID and editable message ID
            migrate(
                migrator.add_column("msgjson", "last_try_timestamp", MsgJson.last_try_timestamp),
            )

    @staticmethod
    def refresh_msg_json():
        query = MsgJson.update(tried=0)
        query.execute()

    @staticmethod
    def get_msg_json(uid) -> Optional[MsgJson]:
        try:
            return MsgJson.select() \
                .where(MsgJson.uid == uid).first()
        except DoesNotExist:
            return None

    def set_msg_json(self, uid, json) -> Optional[MsgJson]:
        msg_json = self.get_msg_json(uid)
        if msg_json is not None:
            msg_json.json = json
            msg_json.save()
            return msg_json
        else:
            return MsgJson.create(uid=uid,
                                  json=json,
                                  tried=0)

    @staticmethod
    def take_msg_json() -> Optional[MsgJson]:
        try:
            msg_json: MsgJson = MsgJson.select() \
                .where(int(time.time()) - MsgJson.last_try_timestamp > 5) \
                .order_by(MsgJson.tried) \
                .first()
            if msg_json is not None:
                msg_json.tried = msg_json.tried + 1
                msg_json.last_try_timestamp = int(time.time())
                msg_json.save()
                return msg_json
            else:
                return None
        except DoesNotExist:
            return None

    @staticmethod
    def take_all_msg_json() -> Optional[list[MsgJson]]:
        try:
            query = MsgJson.select() \
                .where(int(time.time()) - MsgJson.last_try_timestamp > 5) \
                .order_by(MsgJson.tried)
            msg_json_list = list(query)
            if len(msg_json_list) > 0:
                for msg_json in msg_json_list:
                    msg_json.tried = msg_json.tried + 1
                    msg_json.last_try_timestamp = int(time.time())
                    msg_json.save()
                return msg_json_list
            else:
                return None
        except DoesNotExist:
            return None

    @staticmethod
    def resort_msg_json(uid):
        return MsgJson.delete() \
            .where(MsgJson.uid == uid).execute()

    @staticmethod
    def get_slave_chat_info(slave_channel_id: Optional[ModuleID] = None,
                            slave_chat_uid: Optional[ChatID] = None,
                            slave_chat_group_id: Optional[ChatID] = None
                            ) -> Optional[SlaveChatInfo]:
        """
        Get cached slave chat info from database.

        Returns:
            SlaveChatInfo|None: The matching slave chat info, None if not exist.
        """
        if slave_channel_id is None or slave_chat_uid is None:
            raise ValueError("Both slave_channel_id and slave_chat_id should be provided.")
        try:
            return SlaveChatInfo.select() \
                .where((SlaveChatInfo.slave_channel_id == slave_channel_id) &
                       (SlaveChatInfo.slave_chat_uid == slave_chat_uid) &
                       (SlaveChatInfo.slave_chat_group_id == slave_chat_group_id)).first()
        except DoesNotExist:
            return None

    def set_slave_chat_info(self, chat_object: 'ETMChatType') -> SlaveChatInfo:
        """
        Insert or update slave chat info entry

        Args:
            chat_object (ETMChatType): Chat object for pickling

        Returns:
            SlaveChatInfo: The inserted or updated row
        """
        slave_channel_id = chat_object.module_id
        slave_channel_name = chat_object.module_name
        slave_channel_emoji = chat_object.channel_emoji
        slave_chat_uid = chat_object.uid
        slave_chat_name = chat_object.name
        slave_chat_alias = chat_object.alias
        slave_chat_type = chat_object.chat_type_name
        parent_chat: Optional['ETMChatType'] = getattr(chat_object, 'chat', None)
        slave_chat_group_id: Optional[ChatID]
        if parent_chat:
            slave_chat_group_id = parent_chat.uid
        else:
            slave_chat_group_id = None

        chat_info = self.get_slave_chat_info(slave_channel_id=slave_channel_id,
                                             slave_chat_uid=slave_chat_uid,
                                             slave_chat_group_id=slave_chat_group_id)
        if chat_info is not None:
            chat_info.slave_channel_name = slave_channel_name
            chat_info.slave_channel_emoji = slave_channel_emoji
            chat_info.slave_chat_name = slave_chat_name
            chat_info.slave_chat_alias = slave_chat_alias
            chat_info.slave_chat_type = slave_chat_type
            chat_info.pickle = chat_object.pickle
            chat_info.save()
            return chat_info
        else:
            return SlaveChatInfo.create(slave_channel_id=slave_channel_id,
                                        slave_channel_name=slave_channel_name,
                                        slave_channel_emoji=slave_channel_emoji,
                                        slave_chat_uid=slave_chat_uid,
                                        slave_chat_group_id=slave_chat_group_id,
                                        slave_chat_name=slave_chat_name,
                                        slave_chat_alias=slave_chat_alias,
                                        slave_chat_type=slave_chat_type,
                                        pickle=chat_object.pickle)

    @staticmethod
    def delete_slave_chat_info(slave_channel_id: ModuleID, slave_chat_uid: ChatID, slave_chat_group_id: ChatID = None):
        return SlaveChatInfo.delete() \
            .where((SlaveChatInfo.slave_channel_id == slave_channel_id) &
                   (SlaveChatInfo.slave_chat_uid == slave_chat_uid) &
                   (SlaveChatInfo.slave_chat_group_id == slave_chat_group_id)).execute()
