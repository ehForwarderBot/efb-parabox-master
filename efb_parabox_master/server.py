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
        self.loop = asyncio.new_event_loop()

        threading.Thread(target=self.run_main).start()
        # self.run_main()

    def run_main(self):
        self.loop.run_until_complete(self.server_main())
        self.loop.run_forever()
        # asyncio.run(self.server_main())

    async def server_main(self):
        self.logger.info("Websocket listening at %s : %s", self.host, self.port)
        async with websockets.serve(self.handler, self.host, self.port, max_size=1_000_000_000):
            await asyncio.Future()

    # async def msg_looper(self, websocket):
    #     while True:
    #         msg_json = self.db.take_msg_json()
    #         if msg_json is not None:
    #             self.logger.info("Get 1 message to send , tried %s times", msg_json.tried)
    #             await self.send_message(websocket, msg_json.json)
    #         else:
    #             self.logger.info("no message to send, sleep 2s")
    #             await asyncio.sleep(2)
    #
    #         await asyncio.sleep(self.sending_interval)

    def send_all_failed_msg(self):
        self.loop.create_task(self.async_send_all_failed_msg())
        # self.loop.run_until_complete(self.async_send_all_failed_msg())
        # asyncio.run(self.async_send_all_failed_msg())


    async def async_send_all_failed_msg(self):
        self.logger.info("Send all failed msg...")
        failed_msg_jsons = self.db.take_all_msg_json()
        self.logger.info("Get %s failed msgs...", len(failed_msg_jsons))
        for index, msg_json in enumerate(failed_msg_jsons, start=1):
            self.logger.info("Send %s/%s failed msg, tried %s times", index, len(failed_msg_jsons), msg_json.tried)
            await self.async_send_message(msg_json.json)

    async def handler(self, websocket, path):
        if len(self.websocket_users) == 0:
            try:
                await self.check_user_permit(websocket)
                await self.recv_user_msg(websocket)
                # recv_task = asyncio.create_task(self.recv_user_msg(websocket))
                # loop_task = asyncio.create_task(self.msg_looper(websocket))
                # await recv_task
                # await loop_task
            except websockets.ConnectionClosed:
                self.logger.info("ConnectionClosed... %s", path)
                self.websocket_users.remove(websocket)
                self.logger.info("Websocket_users: %s", len(self.websocket_users))
            except websockets.InvalidState:
                self.logger.info("InvalidState...")
                self.logger.info("Websocket_users: %s", len(self.websocket_users))
            except Exception as e:
                self.logger.info("Exception Name: %s: %s", type(e).__name__, e)
                self.websocket_users.remove(websocket)
                self.logger.info("Websocket_users: %s", len(self.websocket_users))
        else:
            self.logger.info("Already has a user, reject new user")

    async def check_user_permit(self, websocket):
        token = self.channel.config.get("token")
        while True:
            timeout = 10
            try:
                recv_str = await asyncio.wait_for(websocket.recv(), timeout)
                if recv_str == token:
                    self.logger.info("WebSocket client connected: %s", websocket)
                    self.websocket_users.add(websocket)
                    self.logger.debug("Websocket_users: %s", len(self.websocket_users))
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
                return False

    async def recv_user_msg(self, websocket):
        self.logger.info("recv user msg...")
        while True:
            recv_text = await websocket.recv()
            # self.logger.debug("recv_text: %s", recv_text)
            json_obj = json.loads(recv_text)
            self.channel.master_messages.process_parabox_message(json_obj)
            # await asyncio.sleep(0.1)

    def pulling(self):
        pass

    def graceful_stop(self):
        self.logger.debug("Websocket server stopped")
        self.loop.stop()

    def send_message(self, json_str):
        # self.loop.run_until_complete(self.async_send_message(json_str))
        self.loop.create_task(self.async_send_message(json_str))
        # asyncio.run(self.async_send_message(json_str))

    async def async_send_message(self, json_str):
        for websocket in self.websocket_users:
            self.logger.debug("sending ws to: %s", websocket)
            await websocket.send(
                json.dumps({
                    "type": "message",
                    "data": json_str
                })
            )
            await asyncio.sleep(self.sending_interval)

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
