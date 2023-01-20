import asyncio
import json
import threading
from queue import Queue
from typing import TYPE_CHECKING

import nest_asyncio
import websockets

if TYPE_CHECKING:
    from . import ParaboxChannel


class FcmClient:
    def __init__(self, channel: 'ParaboxChannel'):
        self.channel = channel
        self.config = channel.config
        self.logger = channel.logger
        self.url = "ws://api.parabox.ojhdt.dev:8080/ws"
        self.fcm_token = self.config.get('fcm_token')
        self.sending_interval = channel.config.get("sending_interval")

        if channel.config.get("enable_fcm", False) is False:
            return

        self.loop = asyncio.new_event_loop()
        self.msg_temp = Queue()

        # self.server = websockets.connect(self.url)
        ws_thread = threading.Thread(target=self.run_main)
        # msg_thread = threading.Thread(target=self.msg_main)
        ws_thread.setDaemon(True)
        # msg_thread.setDaemon(True)
        ws_thread.start()
        # msg_thread.start()

    def run_main(self):
        try:
            asyncio.set_event_loop(self.loop)
            nest_asyncio.apply()
            self.logger.info("Websocket connecting at %s", self.url)
            self.loop.run_until_complete(self.server())
        except Exception as e:
            self.logger.info("Exception Name: %s: %s", type(e).__name__, e)

    async def server(self):
        async with websockets.connect(self.url) as websocket:
            self.logger.info("Websocket connected")
            asyncio.create_task(self.recv_msg(websocket))
            # asyncio.create_task(self.msg_looper(websocket))
            # await self.recv_msg(websocket)
            await self.msg_looper(websocket)
            # self.logger.info("Websocket server stopped")
            # self.loop.stop()

    # def msg_main(self):
    #     asyncio.set_event_loop(self.loop)
    #     nest_asyncio.apply()
    #     self.loop.run_until_complete(self.msg_looper(self.msg_temp))

    async def msg_looper(self, websocket):
        self.logger.info("Websocket msg_looper started")
        while True:
            try:
                if not self.msg_temp.empty():
                    msg = self.msg_temp.get()
                    self.logger.info("Sending message, msg_temp_size: %s", self.msg_temp.qsize())
                    await self.async_send_message(websocket, msg)
                    self.logger.info("Message sent")
                await asyncio.sleep(self.sending_interval)
            except Exception as e:
                pass

    async def async_send_message(self, websocket, json_str):
        await websocket.send(
            json.dumps({
                "type": "server",
                "data": json_str,
                "token": self.fcm_token
            })
        )

    def send(self, data: str):
        self.logger.debug('Sending FCM message: %s', data)
        self.msg_temp.put(data)

    async def recv_msg(self, websocket):
        self.logger.info("Websocket recv_msg started")
        while True:
            recv_text = await websocket.recv()
            self.logger.debug('Received FCM message: %s', recv_text)
            json_obj = json.loads(recv_text)
            self.channel.master_messages.process_parabox_message(json_obj)

    def graceful_stop(self):
        self.logger.debug("Websocket server stopped")
        self.loop.stop()
