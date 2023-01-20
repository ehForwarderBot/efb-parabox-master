# import asyncio
# import json
# import random
# import string
#
# from typing import TYPE_CHECKING
#
# import firebase_admin
# from ehforwarderbot import utils as efb_utils
# from firebase_admin import credentials
#
# from slixmpp.xmlstream.stanzabase import ElementBase
# from slixmpp import ClientXMPP
# from slixmpp.stanza import Message
# from slixmpp.xmlstream import register_stanza_plugin
# from slixmpp.xmlstream.handler import Callback
# from slixmpp.xmlstream.matcher import StanzaPath
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
#         asyncio.set_event_loop(asyncio.new_event_loop())
#
#         self.xmpp = GCM(user, password, self.logger)
#         self.xmpp.add_event_handler(XMPPEvent.CONNECTED, self.onSessionStart)
#         self.xmpp.add_event_handler(XMPPEvent.DISCONNECTED, self.onDisconnect)
#         self.xmpp.add_event_handler(XMPPEvent.RECEIPT, self.onReceipt)
#         self.xmpp.add_event_handler(XMPPEvent.MESSAGE, self.onMessage)
#         # self.xmpp.connect(('fcm-preprod.googleapis.com', 5236), use_ssl=True)
#         self.xmpp.connect(("fcm-xmpp.googleapis.com", 5236), use_ssl=True)  # test environment
#
#         while True:
#             self.xmpp.process(forever=True)
#
#         # self.app = xmpp.Client(server="fcm-xmpp.googleapis.com", port=5235, debug=[])
#         # self.app.connect(secure=1)
#         # self.app.auth(user=user, password=password, sasl='PLAIN')
#         # self.app.event = self.event
#
#     def onAcknowledge(self, error, message_id, _from):
#         if error is not None:
#             self.logger.info('not acknowledged by GCM')
#
#         self.logger.info('id - {0} : from - {1}'.format(message_id, _from))
#
#
#     def onDisconnect(self, draining):
#         self.logger.info('inside onDisconnect')
#         self.xmpp.connect(('fcm-xmpp.googleapis.com', 5236), use_ssl=True)
#
#     def onSessionStart(self, queue_length):
#         self.logger.info('inside onSessionStart {0}'.format(queue_length))
#         data = {'key1': 'value1'}
#         options = {'delivery_receipt_requested': True}
#         self.xmpp.send_gcm('your_device_token', data, options, self.onAcknowledge)
#
#     def onReceipt(self, data):
#         self.logger.info('inside onReceipt {0}'.format(data))
#
#     def onMessage(self, data):
#         self.logger.info('inside onMessage {0}'.format(data))
#
#
# class GCMMessageType(object):
#     ACK = 'ack'
#     NACK = 'nack'
#     CONTROL = 'control'
#     RECEIPT = 'receipt'
#
#
# class XMPPEvent(object):
#     CONNECTED = 'client_connected'
#     DISCONNECTED = 'client_disconnected'
#     ERROR = 'client_error'
#     RECEIPT = 'client_receipt'
#     MESSAGE = 'client_message'
#     ACK = 'ack'
#     NACK = 'nack'
#
#
# class GCMMessage(ElementBase):
#     name = 'gcm'
#     namespace = 'google:mobile:data'
#     plugin_attrib = 'gcm'
#     interfaces = set('json_data')
#     sub_interfaces = interfaces
#     data = {}
#
#     def __init__(self, xml, parent):
#         ElementBase.__init__(self, xml, parent)
#         json_str = xml.text
#         self.data = json.loads(json_str)
#
#     @property
#     def is_error(self):
#         if 'error' in list(self.data.keys()):
#             return True
#         return False
#
#     @property
#     def error_description(self):
#         if 'error_description' in list(self.data.keys()):
#             if self.data.get('error_description') != '':
#                 return ' %s: %s' % (self.data.get('error', ''), self.data.get('error_description', ''))
#             else:
#                 return self.data.get('error')
#         return ''
#
#     @property
#     def message_id(self):
#         return self.data.get('message_id', '')
#
#     @property
#     def message_type(self):
#         return self.data.get('message_type', '')
#
#     @property
#     def control_type(self):
#         return self.data.get('control_type', '')
#
#
# class GCM(ClientXMPP):
#
#     def __init__(self, id, password, logger):
#         ClientXMPP.__init__(self, id, password, sasl_mech='PLAIN')
#         self.auto_reconnect = True
#         self.connecton_draining = False
#         self.MSG = '<message><gcm xmlns="google:mobile:data">{0}</gcm></message>'
#         self.QUEUE = []
#         self.ACKS = {}
#         self.logger = logger
#
#         register_stanza_plugin(Message, GCMMessage)
#
#         self.register_handler(
#             Callback('GCM Message', StanzaPath('message/gcm'), self.on_gcm_message)
#         )
#
#         self.add_event_handler('session_start', self.session_start)
#         self.add_event_handler('disconnected', self.on_disconnected)
#
#     @property
#     def connection_draining(self):
#         """ This is a fix to the mispelling connecton_draining,
#         "i" is missing, but this is for not breaking the already
#         working implementations of the module. """
#
#         return self.connecton_draining
#
#     @connection_draining.setter
#     def connection_draining(self, value):
#         self.connecton_draining = value
#
#     def on_gcm_message(self, msg):
#         self.logger.debug('inside on_gcm_message {0}'.format(msg))
#         data = msg['gcm']
#         self.logger.debug('Msg: {0}'.format(data))
#         if data.message_type == GCMMessageType.NACK:
#             self.logger.debug('Received NACK for message_id: %s with error, %s' % (data.message_id, data.error_description))
#             if data.message_id in self.ACKS:
#                 self.ACKS[data.message_id](data.error_description, data)
#                 del self.ACKS[data.message_id]
#
#         elif data.message_type == GCMMessageType.ACK:
#             self.logger.debug('Received ACK for message_id: %s' % data.message_id)
#             if data.message_id in self.ACKS:
#                 self.ACKS[data.message_id](None, data)
#                 del self.ACKS[data.message_id]
#
#         elif data.message_type == GCMMessageType.CONTROL:
#             self.logger.debug('Received Control: %s' % data.control_type)
#             if data.control_type == 'CONNECTION_DRAINING':
#                 self.connecton_draining = True
#
#         elif data.message_type == GCMMessageType.RECEIPT:
#             self.logger.debug('Received Receipts for message_id: %s' % data.message_id)
#             self.event(XMPPEvent.RECEIPT, data)
#
#         else:
#             if data['from']:
#                 self.send_gcm({
#                                 'to': data['from'],
#                                 'message_id': data.message_id,
#                                 'message_type': 'ack',
#                             })
#             self.event(XMPPEvent.MESSAGE, data)
#
#     def session_start(self, event):
#         self.logger.debug("session started")
#
#         if self.connecton_draining == True:
#             self.connecton_draining = False
#             for i in reversed(self.QUEUE):
#                 self.send_gcm(i)
#             self.QUEUE = []
#
#         self.event(XMPPEvent.CONNECTED, len(self.QUEUE))
#
#     def on_disconnected(self, event):
#         self.logger.debug("Disconnected")
#         self.event(XMPPEvent.DISCONNECTED, self.connecton_draining)
#
#     def send_gcm(self, to, data, options, cb, ttl=60):
#         message_id = self.random_id()
#         payload = {
#             'to': to,
#             'message_id': message_id,
#             'data': data,
#             'time_to_live': int(ttl),
#             'delivery_receipt_requested': True
#         }
#
#         if options:
#             for key, value in options.items():
#                 payload[key]= value
#
#         if cb:
#             self.ACKS[message_id] = cb
#
#         if self.connecton_draining == True:
#             self.QUEUE.append(payload)
#         else:
#             self.send_raw(self.MSG.format(json.dumps(payload)))
#
#         return message_id
#
#     def random_id(self):
#         rid = ''
#         for x in range(24): rid += random.choice(string.ascii_letters + string.digits)
#         return