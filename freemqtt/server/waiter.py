# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import time
import logging
import struct

from io import BytesIO
from typing import Tuple, Dict
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.iostream import StreamClosedError

from  .authplugin import AuthPlugin
from  .memdb import MemDB
from .common import State, PacketClass
from .authplugin import AuthPlugin

from ..mqttp.packet import Packet
from ..mqttp.connect import Connect
from ..mqttp.connack import Connack
from ..mqttp.publish import Publish
from ..mqttp.puback import Puback
from ..mqttp.pubrec import Pubrec
from ..mqttp.pubrel import Pubrel
from ..mqttp.pubcomp import Pubcomp
from ..mqttp.subscribe import Subscribe
from ..mqttp.suback import Suback
from ..mqttp.unsubscribe import Unsubscribe
from ..mqttp.unsuback import Unsuback
from ..mqttp.pingreq import Pingreq
from ..mqttp.pingresp import Pingresp
from ..mqttp.disconnect import Disconnect
from ..mqttp.auth import Auth

from ..mqttp import reason_code as ReasonCode
from ..mqttp import mask
from ..mqttp.packet import Packet
from ..mqttp import protocol, utils
from ..mqttp.pktype import PacketType
from ..mqttp.property import PropertSet, Property, StringPair
from ..mqttp.reason_code import Reason, validReasoneCode

PUB_SYS_INFO_INTERVAL = 15
INIT_INTERVAL = 8
CLOSING_FOR_EXCEPTION = 6
KEEP_ALIVE_TIMEOUT = 7
CLOSED = 8
FACTOR = 1.5

class Waiter(object):
    def __init__(self, stream, address):
        self.state = State.INITIATED
        self.mem_db = MemDB.instance()
        self.mqtt_connect = None
        self.mqtt_session = None
        self.protocol_version = protocol.MQTT311

        self.keep_alive = 60
        self.auth_plugin = AuthPlugin()
        self.appid = None
        self.appname = None
        self.last_timestamp = time.time()
        self.stream = stream
        self.remote_ip = address
        self.received_bytes = 0
        self.receive_quota = 0
        self.send_quota = 0

        self.alias2topic_map: Dict[int, str] = {} # for client side { alias: topic }
        self.topic2alias_map: Dict[str, int] = {} # for server side { topic: alias }

        self.handlers = {
            PacketType.CONNECT:     self.connect_handler,
            PacketType.PUBLISH:     self.publish_handler,
            PacketType.PUBACK:      self.puback_handler,
            PacketType.PUBREC:      self.pubrec_handler,
            PacketType.PUBREL:      self.pubrel_handler,
            PacketType.PUBCOMP:     self.pubcomp_handler,
            PacketType.SUBSCRIBE:   self.subscribe_handler,
            PacketType.SUBACK:      self.suback_handler,
            PacketType.UNSUBSCRIBE: self.unsubscribe_handler,
            PacketType.UNSUBACK:    self.unsuback_handler,
            PacketType.PINGREQ:     self.pingreq_handler,
            PacketType.DISCONNECT:  self.disconnect_handler,
            PacketType.AUTH:        self.auth_handler,
        }

    async def connect_timout(self):
        await gen.sleep(INIT_INTERVAL)

    async def publish_system_info(self):
    	while True:
            await gen.sleep(PUB_SYS_INFO_INTERVAL)
            await self.mem_db.update_sys_info_topic()

    async def read_pktype_flags(self) -> Tuple[int, int]:
        buff = await self.stream.read_bytes(1)
        b, = struct.unpack("!B", buff)
        flags = b & mask.Flags
        pktype = b >> 4
        return (pktype, flags)

    async def read_remaining_length(self) -> int:
        val = 0; mtp = 1
        while True:
            buff = await self.stream.read_bytes(1)
            b, = struct.unpack("!B", buff)
            val += (b & 0x7F) * mtp
            mtp *= 128
            if mtp > 2097152: # 128*128*128 = 2^21
                return None
            if b & 0x80:
                continue
            else:
                break
        return val

    async def recv_mqtt_packet(self) -> Packet:
        # read packet type & flags (fixed header first byte)
        pktype, flags = await self.read_pktype_flags()
        self.received_bytes += 1 
        if not pktype in self.handlers:
            logging.error(f"Invalid packet type: {pktype}")
            return None
        
        pktype = PacketType(pktype)
        logging.info(f"{pktype.name} flags:0x{flags:02X}")

        # read remaining lenght
        remain_len = await self.read_remaining_length()
        if not remain_len:
            logging.error("Invalid remaining length")
            return None
        
        # read remaining data    
        data = await self.stream.read_bytes(remain_len)
        self.received_bytes += remain_len 
        # unpack remaining data
        packet = PacketClass.get(pktype)(ver=self.protocol_version)
        packet.set_flags(flags)
        reader = BytesIO(data)
        if not packet.unpack(reader):
            packet = None
        reader.close()
        return packet

    async def start_serving(self) -> None:
        logging.info(f"TCP connecting from {self.remote_ip}")
        while True:
            try:
                packet = await self.recv_mqtt_packet()
                if packet:
                    await self.handle_packet(packet)
                else:
                    if self.state == State.CONNECTED and self.protocol_version==protocol.MQTT50:
                        await self.send_disconnect(Reason.ProtocolError)
                    self.stream.close()
            except StreamClosedError:
                await self.closed_handler()
                self.state = State.CLOSED
                logging.error(f"remote: {self.remote_ip} be closed")
                break
            
    async def handle_packet(self, packet: Packet) -> None:
        handler = self.handlers[packet.get_type()]
        await handler(packet)

    async def connect_handler(self, packet: Connect) -> None:
        if self.state != State.INITIATED:
            self.stream.close()            
            logging.error(f"Error state:{self.state} remote ip:{self.remote_ip}")
            return
        self.state = State.CONNECTING
        self.connect = packet
        self.protocol_version = packet.get_version()
        rcode, self.username, self.appid, self.appname =  self.auth_plugin.auth_token(packet.username, packet.password)
        logging.info(f"r CONNECT (clientid:{packet.clientid} clean_start:{packet.clean_start} keep_alive:{packet.keep_alive} ack_code:{rcode}")
        
        ack_flags = 0x00
        if rcode == ReasonCode.Success:
            self.pub_acl = self.auth_plugin.pub_acl_list()
            self.sub_acl = self.auth_plugin.sub_acl_list()
            self.state = State.CONNECTED
            if self.mqttdb.session_present(packet.clientid):
                ack_flags = 0 if packet.clean_start else 1
                session = self.mqttdb.get_session(packet.clientid)
                logging.error(f"session is present: {packet.clientid}")
                if session.is_active():
                    context = self.mqttdb.get_context(packet.clientid)
                    context.state = KICKOUT
                    context.stream.close()
                    logging.error(f"KICKOUT: clientid:%{packet.clientid} ip:{context.remote_ip}")

            # check if exceed the connect maximum
            # to do

            self.mqttdb.add_session(self)
            appc = self.mqttdb.get_app_config(self.appid)
            self.receive_quota = appc.receive_maximum
            self.send_quota = packet.receive_maximum()
            if packet.keep_alive:
                self.keep_alive = packet.keep_alive
            IOLoop.current().spawn_callback(self.monitor_timeout)
            await self.send_connack(ack_flags, rcode)
        else:
            await self.send_connack(ack_flags, rcode)
            self.stream.close()
            logging.info("Connection be closed.")

        return

    async def send_connack(self, ack_flags: int, rcode: int) -> None:
        packet = Connack(self.protocol_version)
        if self.protocol_version == protocol.MQTT50 and rcode==ReasonCode.Success:
            appconfig = self.mqttdb.get_app_config(self.appid)
            # Session Expiry Interval
            sei = self.connect.propset.get(Session_Expiry_Interval)
            if not sei:
                sei = appconfig.session_expiry_interval
            packet.set_session_expiry_interval(sei)
            # Receive Maximum
            packet.set_receive_maximum(appconfig.receive_maximum)
            # Maximum QoS
            packet.set_maximum_qos(appconfig.maximum_qos)
            # Retain Available
            packet.set_retain_available(appconfig.retain_available)
            # Maximum Packet Size
            packet.set_maximum_packet_size(appconfig.maximum_packet_size)
            # Assigned Client Identifier
            if self.connect.assigned_id:
                packet.set_assiged_client_identifier(self.connect.clientid)
            # Topic Alias Maximum
            packet.set_topic_alias_maximum(appconfig.topic_alias_maximum)
            # Reason String
            packet.set_reason_string(ReasonCode.reason_description(rcode))
            # Wildcard Subscription Available
            packet.set_wildcard_subscription_available(appconfig.wildcard_subscription_available)
            # Subscription Identifiers Available
            packet.set_subscription_identifiers_available(appconfig.subscription_identifiers_available)
            # Shared Subscription Available
            packet.set_shared_subscription_available(appconfig.shared_subscription_available)
            # Server Keep Alive
            packet.set_server_keep_alive(appconfig.server_keep_alive)
            self.keep_alive = appconfig.server_keep_alive
            # Response Information
            if self.connect.request_response_information():
                packet.set_response_information(appconfig.response_information)

            # No implement below
            # Server Reference
            # Authentication Method
            # Authentication Data

        packet.set_ack_flags(ack_flags)
        packet.set_reason_code(rcode)
        
        data = packet.full_pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info(f"s CONNACK client_id:{client_id}")

    async def publish_handler(self, packet: Publish) -> None:
        if self.state != CONNECTED:
            logging.error(f"Error state:{self.state} remote ip:{self.remote_ip}")
            if self.protocol_version == protocol.MQTT50:
                await self.send_disconnect(ReasonCode.ProtocolError)
            self.stream.close()
            logging.info("Connection be closed.")
            return

        appc = self.mqttdb.get_app_config(self.appid)
        qos = packet.get_qos()
        pid = packet.get_pid()
        topic = packet.topic
        retain = packet.get_retain()
        payload_len = len(packet.payload)
        clientid = self.connect.clientid
        logging.info(f"r PUBLISH pid:{pid} qos:{qos} topic:{topic} retain:{retain} paylaod_len:{payload_len} from client_id:{clientid}")

        # handle topic alias
        if self.protocol_version==protocol.MQTT50:
            alias = packet.topic_alias()
            if alias == 0 or alias > appc.topic_alias_maximum:
                await self.send_disconnect(ReasonCode.InvalidTopicAlias)
                self.stream.close()
                logging.error(f"Invalid topic alias:{alias} topic:{topic}")
                return
            if alias:
                if topic:
                    self.alias2topic_map[alias] = topic
                elif alias in self.alias2topic_map:
                    topic = self.alias2topic_map[alias]
                    packet.set_topic(topic)
                else:                
                    await self.send_disconnect(ReasonCode.ProtocolError)
                    self.stream.close()
                    logging.error(f"Protocol error topic alias:{alias} topic:none")
                    return

        if qos > 0 and self.receive_quota == 0:
            appc = self.mqttdb.get_app_config(self.appid)
            if self.protocol_version==protocol.MQTT50:
                await self.send_disconnect(ReasonCode.ReceiveMaximumExceeded)
            self.stream.close()
            logging.error(f"Receive Maximum Exceeded: {appc.receive_maximum}")
            return

        # QoS case 
        if qos == 1:
            self.receive_quota -= 1
            await self.send_puback(pid)
            self.receive_quota += 1
        elif qos == 2:
            self.receive_quota -= 1
            await self.send_pubrec(pid)
        
    async def send_disconnect(self, rcode: int) -> None:
        packet = Disconnect(self.protocol_version)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
            appconfig = self.mqttdb.get_app_config(self.appid)
            # Session Expiry Interval
            sei = self.connect.propset.get(Session_Expiry_Interval)
            if not sei:
                sei = appconfig.session_expiry_interval
            packet.set_session_expiry_interval(sei)
            # Reason String
            packet.set_reason_string(ReasonCode.reason_description(rcode))

        data = packet.full_pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info(f"s DISCONNECT client_id:{client_id}")

    async def send_puback(self, rcode: int) -> None:
        packet = Puback(self.protocol_version)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
            # Reason String
            packet.set_reason_string(ReasonCode.reason_description(rcode))

        data = packet.full_pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info(f"s PUBACK client_id:{client_id}")
