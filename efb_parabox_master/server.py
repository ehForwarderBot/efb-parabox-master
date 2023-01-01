# coding=utf-8

import itertools
import json
import logging
import time
from json import JSONDecodeError
from typing import TYPE_CHECKING
import threading

from ehforwarderbot import Status
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, MessageReactionsUpdate

import asyncio
from asyncio.exceptions import TimeoutError
import websockets

# import nest_asyncio
#
# nest_asyncio.apply()

if TYPE_CHECKING:
    from . import ParaboxChannel
    from .db import DatabaseManager


# def get_or_create_eventloop():
#     try:
#         return asyncio.get_event_loop()
#     except RuntimeError as ex:
#         if "There is no current event loop in thread" in str(ex):
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             return asyncio.get_event_loop()


class ServerManager:
    def __init__(self, channel: 'ParaboxChannel'):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.channel: 'ParaboxChannel' = channel
        self.db: 'DatabaseManager' = channel.db

        self.host = channel.config.get("host")
        self.port = channel.config.get("port")
        self.sending_interval = channel.config.get("sending_interval")

        self.websocket_users = set()

        # run self.run_main in another thread
        self.ws_loop = asyncio.new_event_loop()
        self.msg_loop = asyncio.new_event_loop()
        self.ws_thread = threading.Thread(target=self.run_server, daemon=True).start()
        self.msg_thread = threading.Thread(target=self.run_looper, daemon=True).start()

    def pulling(self):
        pass

    def graceful_stop(self):
        self.logger.debug("Websocket server stopped")
        self.ws_loop.stop()
        self.ws_loop.stop()

    async def msg_looper(self):
        while True:
            # check self.websocket_users empty
            if len(self.websocket_users) == 0:
                self.logger.debug("no websocket user, sleep 1s")
                await asyncio.sleep(1)
                continue

            msg_json = self.db.take_msg_json()
            if msg_json is not None:
                self.logger.info("Get 1 message to send , tried %s times", msg_json.tried)
                await self.send_message(msg_json.json)

            await asyncio.sleep(self.sending_interval)

    async def send_message(self, json_str):
        self.logger.debug("websocket_users: %s", len(self.websocket_users))
        for websocket in self.websocket_users.copy():
            self.logger.debug("sending ws to: %s", websocket)
            await websocket.send(
                json.dumps({
                    "type": "message",
                    "data": json_str
                })
            )

    def send_status(self, status: 'Status'):
        if isinstance(status, ChatUpdates):
            self.logger.debug("Received chat updates from channel %s", status.channel)
            pass
        elif isinstance(status, MemberUpdates):
            self.logger.debug("Received member updates from channel %s about group %s",
                              status.channel, status.chat_id)
            pass
        elif isinstance(status, MessageRemoval):
            self.logger.debug("Received message removal request from channel %s on message %s",
                              status.source_channel, status.message)
            pass
        elif isinstance(status, MessageReactionsUpdate):

            pass
        else:
            self.logger.debug('Received an unsupported type of status: %s', status)

    def run_server(self):
        self.logger.info("Websocket listening at %s : %s", self.host, self.port)
        asyncio.set_event_loop(self.ws_loop)
        self.ws_loop.run_until_complete(self.server_main())

    async def server_main(self):
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()

    def run_looper(self):
        asyncio.set_event_loop(self.msg_loop)
        self.msg_loop.run_until_complete(self.msg_looper())

    def run_main(self):
        # run self.server_main and self.msg_looper without blocking
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(self.server_main(), self.msg_looper()))

    async def handler(self, websocket, path):
        while True:
            try:
                await self.check_user_permit(websocket)
                await self.recv_user_msg(websocket)
            except websockets.ConnectionClosed:
                self.logger.debug("ConnectionClosed... %s", path)
                self.websocket_users.remove(websocket)
                self.logger.debug("websocket_users: %s", len(self.websocket_users))
                break
            except websockets.InvalidState:
                self.logger.debug("InvalidState...")
                self.logger.debug("websocket_users: %s", len(self.websocket_users))
                break
            except Exception as e:
                self.logger.debug("Exception Name: %s: %s", type(e).__name__, e)
                self.websocket_users.remove(websocket)
                self.logger.debug("websocket_users: %s", len(self.websocket_users))
                break

    async def check_user_permit(self, websocket):
        token = self.channel.config.get("token")
        self.websocket_users.add(websocket)
        self.logger.debug("websocket_users: %s", len(self.websocket_users))
        while True:
            timeout = 10
            try:
                recv_str = await asyncio.wait_for(websocket.recv(), timeout)
                self.logger.debug("recv_str: %s", recv_str)
                if recv_str == token:
                    self.logger.info("WebSocket client connected: %s", websocket)
                    await websocket.send(
                        json.dumps({
                            "type": "code",
                            "data": {
                                "code": 4000,
                                "msg": "success"
                            }
                        })
                    )
                    return True
                else:
                    self.logger.info("WebSocket client token incorrect: %s", websocket)
                    await websocket.send(
                        json.dumps({
                            "type": "code",
                            "data": {
                                "code": 1000,
                                "msg": "token incorrect"
                            }
                        })
                    )
                    self.websocket_users.remove(websocket)
                    return False
            except TimeoutError as e:
                self.logger.info("WebSocket client token timeout: %s", websocket)
                await websocket.send(
                    json.dumps({
                        "type": "code",
                        "data": {
                            "code": 1001,
                            "msg": "timeout"
                        }
                    })
                )
                self.websocket_users.remove(websocket)
                return False

    async def recv_user_msg(self, websocket):
        self.logger.debug("websocket_users: %s", len(self.websocket_users))
        self.logger.debug("recv user msg...")
        while True:
            recv_text = await websocket.recv()
            # self.logger.debug("recv_text: %s", recv_text)
            json_obj = json.loads(recv_text)
            self.channel.master_messages.process_parabox_message(json_obj)
