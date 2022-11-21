from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any

from ehforwarderbot import Message, coordinator, MsgType, Chat, Channel
from ehforwarderbot.chat import ChatMember
from ehforwarderbot.message import MessageAttribute, MessageCommands, Substitutions
from ehforwarderbot.types import Reactions, MessageID


class EPMMsg(Message):
    def __init__(self, attributes: Optional[MessageAttribute] = None, author: ChatMember = None, chat: Chat = None,
                 commands: Optional[MessageCommands] = None, deliver_to: Channel = None, edit: bool = False,
                 edit_media: bool = False, file: Optional[BinaryIO] = None, filename: Optional[str] = None,
                 is_system: bool = False, mime: Optional[str] = None, path: Optional[Path] = None,
                 reactions: Reactions = None, substitutions: Optional[Substitutions] = None,
                 target: 'Optional[Message]' = None, text: str = "", type: MsgType = MsgType.Unsupported,
                 uid: Optional[MessageID] = None, vendor_specific: Dict[str, Any] = None):
        super().__init__(attributes=attributes, chat=chat, author=author, commands=commands, deliver_to=deliver_to,
                         edit=edit, edit_media=edit_media, file=file, filename=filename, is_system=is_system, mime=mime,
                         path=path, reactions=reactions, substitutions=substitutions, target=target, text=text,
                         type=type, uid=uid, vendor_specific=vendor_specific)

