import itertools
import logging
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


class ServerManager:

    def __init__(self, channel: 'ParaboxChannel'):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.channel: 'ParaboxChannel' = channel
        self.host = channel.config.get("host")
        self.port = channel.config.get("port")

        self.websocket_users = set()

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.run_server, daemon=True).start()

    def pulling(self):
        pass

    def graceful_stop(self):
        self.logger.debug("Websocket server stopped")
        self.loop.stop()

    async def send_message(self, json):
        self.logger.debug("websocket_users: %s", len(self.websocket_users))
        for websocket in self.websocket_users:
            self.logger.debug("sending ws to: %s", websocket)
            await websocket.send(json)

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
        self.logger.debug("Websocket listening at %s : %s", self.host, self.port)
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handler, self.host, self.port)
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

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
                self.logger.debug("Exception Name: %s", type(e).__name__)
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
                    self.logger.debug("WebSocket client connected: %s", websocket)
                    await websocket.send("4000")
                    return True
                else:
                    self.logger.debug("WebSocket client token incorrect: %s", websocket)
                    await websocket.send("1000")
                    self.websocket_users.remove(websocket)
                    return False
            except TimeoutError as e:
                self.logger.debug("WebSocket client token timeout: %s", websocket)
                await websocket.send("1001")
                self.websocket_users.remove(websocket)
                return False

    async def recv_user_msg(self, websocket):
        self.logger.debug("websocket_users: %s", len(self.websocket_users))
        self.logger.debug("recv user msg...")
        while True:
            recv_text = await websocket.recv()
            self.logger.debug("recv_text: %s, %s", websocket.pong, recv_text)
            response_text = f"recv_text:${websocket.pong}, ${recv_text}"
            await websocket.send(response_text)
