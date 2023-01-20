# import asyncio
# import datetime
# import json
# import random
# import string
# import threading
# from firebase_admin import credentials, messaging
# from queue import Queue
#
# from typing import TYPE_CHECKING
#
# import aioxmpp
# import firebase_admin
# from ehforwarderbot import utils as efb_utils
# from firebase_admin import credentials
#
# from uuid import uuid4
# from aiofcm import FCM, Message, PRIORITY_HIGH
#
# FCM_SERVER_URL = "fcm-xmpp.googleapis.com"
# FCM_SERVER_PORT = 5235
# API_KEY = 'null'
# SENDER_ID = 1
#
# if TYPE_CHECKING:
#     from . import ParaboxChannel
#
#
# class XmppServer:
#     def __init__(self, channel: 'ParaboxChannel'):
#         self.channel = channel
#         self.config = channel.config
#         self.logger = channel.logger
#         cred = credentials.Certificate(path)
#         cred.get_access_token()
#
#         self.fcm_token = self.config.get('fcm_token')
#
#
#         self.loop = asyncio.new_event_loop()
#         self.msg_temp = Queue()
#         asyncio.set_event_loop(self.loop)
#         self.fcm = FCM(SENDER_ID, API_KEY, upstream_callback=self.my_callback)
#         threading.Thread(target=self.main, daemon=True).start()
#
#     async def my_callback(self, device_token, app_name, data):
#         global DEVICE_TOKEN
#
#         self.logger.info("=======================")
#         self.logger.info("Received: %s", data)
#         self.logger.info("=======================")
#
#         txt = data['txt']
#         txt = txt.upper()  # Echo back uppercase txt field
#
#         message = Message(
#             device_token=device_token,
#             data={"txt": txt},
#             message_id=str(uuid4()),  # optional
#             time_to_live=0,  # optional
#             priority=PRIORITY_HIGH,  # optional
#         )
#
#         await self.fcm.send_message(message)
#
#         if txt == "subscribe".upper():
#             DEVICE_TOKEN = device_token
#             print("set DEVICE_TOKEN to", device_token)
#         elif txt == "unsubscribe".upper():
#             DEVICE_TOKEN = None
#             print("unset DEVICE_TOKEN")
#
#     async def run(self, token):
#         while True:
#             if token is not None:
#                 txt = datetime.datetime.now().strftime("%H:%M:%S")
#
#                 message = Message(
#                     device_token=token,
#                     data={"txt": txt},
#                     message_id=str(uuid4()),  # optional
#                     time_to_live=0,  # optional
#                     priority=PRIORITY_HIGH,  # optional
#                 )
#
#                 self.logger.info("Send: %s", txt)
#                 await self.fcm.send_message(message)
#             await asyncio.sleep(5)
#
#     def main(self):
#         asyncio.set_event_loop(self.loop)
#         self.loop.run_until_complete(self.looper())
#
#     async def looper(self):
#         while True:
#             if not self.msg_temp.empty():
#                 msg = self.msg_temp.get()
#                 await self.async_send(msg)
#             await asyncio.sleep(0.1)
#
#     def send(self, data: str):
#         self.msg_temp.put(data)
#
#     async def async_send(self, data: str):
#         message = Message(
#             device_token=self.fcm_token,
#             data={
#                 "dto": data,
#                 "type": "server"
#             },
#         )
#         await self.fcm.send_message(message)
#         self.logger.log(99, 'Successfully sent message')
