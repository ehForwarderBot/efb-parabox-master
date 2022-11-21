import itertools
import logging
from typing import TYPE_CHECKING

from ehforwarderbot import Status
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, MessageReactionsUpdate

import asyncio
import websockets
import nest_asyncio
nest_asyncio.apply()

if TYPE_CHECKING:
    from . import ParaboxChannel


class ServerManager:

    def __init__(self, channel: 'ParaboxChannel'):
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.channel: 'ParaboxChannel' = channel
        host = channel.config.get("host")
        port = channel.config.get("port")
        self.logger.debug("Websocket listening at %s : %s", host, port)

        self.websocket_users = set()

        start_server = websockets.serve(self.handler, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def pulling(self):
        pass

    def graceful_stop(self):
        self.logger.debug("Websocket server stopped")

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

    async def handler(self, websocket, path):
        while True:
            try:
                await self.check_user_permit(websocket)
                await self.recv_user_msg(websocket)
            except websockets.ConnectionClosed:
                self.logger.debug("ConnectionClosed... %s", path)
                self.websocket_users.remove(websocket)
                break
            except websockets.InvalidState:
                self.logger.debug("InvalidState...")
                break
            except Exception as e:
                self.logger.debug("Exception: %s", e)

    async def check_user_permit(self, websocket):
        token = self.channel.config.get("token")
        self.websocket_users.add(websocket)
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
            except websockets.ConnectionClosed as e:
                self.logger.debug("WebSocket client token timeout: %s", websocket)
                await websocket.send("1001")


    async def recv_user_msg(self, websocket):
        self.logger.debug("recv user msg...")
        while True:
            recv_text = await websocket.recv()
            self.logger.debug("recv_text: %s, %s", websocket.pong, recv_text)
            response_text = f"recv_text:${websocket.pong}, ${recv_text}"
            await websocket.send(response_text)