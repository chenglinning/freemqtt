# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import time
import logging
import struct, uuid
from typing import Awaitable, List

from io import BytesIO
from typing import Tuple, Dict
from tornado.ioloop import IOLoop
from tornado import gen
from .config import Config
from .authplugin import AuthPlugin
from .common import State, PacketClass, Topic, TopicFilter, PacketID 
from .common import TopicFilterRegexp, TopicPublishRegexp, SharedTopicRegexp

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

from ..mqttp import mask
from ..mqttp import protocol
from ..mqttp.pktype import PacketType, QoS
from ..mqttp.property import Property
from ..mqttp.reason_code import Reason
from ..transport import TransportClosedError

PUB_SYS_INFO_INTERVAL = 15
INIT_INTERVAL = 10
CLOSING_FOR_EXCEPTION = 6
KEEP_ALIVE_TIMEOUT = 7
CLOSED = 8
FACTOR = 1.5

class Bridge(object):
    def __init__(self, transport, address):
        self.state = State.INITIATED
        self.app = None
        self.nodeid = f'{uuid.uuid1().hex[0:8]}@node'
        self.connect = None
        self.protocol_version = protocol.MQTT50
        self.keep_alive = 20
        self.appid = "bridge@mqtt"
        self.appname = "bridge@mqtt"
        self.token = "tCWqBflYm7Rovt9W+J+oGnATU921Fh1fzoG1qxK/j0M="

        self.last_timestamp = time.time()
        self.transport = transport
        self.remote_ip = address
        self.received_bytes = 0
        self.receive_quota = 0
        self.send_quota = 0
        self.alias_maximum = 0

        self.alias2topic_map: Dict[int, Topic] = {} # for client side { alias: topic }
        self.topic2alias_map: Dict[Topic, int] = {} # for server side { topic: alias }
        self.disconnect_rcode = Reason.Success

        self.handlers = {
            PacketType.CONNACK:     self.connack_handler,
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

    async def read_pktype_flags(self) -> Awaitable[Tuple[int, int]]:
        buff = await self.transport.read_bytes(1)
        b, = struct.unpack("!B", buff)
        flags = b & mask.Flags
        pktype = b >> 4
        return (pktype, flags)

    async def read_remaining_length(self) -> Awaitable[int]:
        val = 0; mtp = 1
        while True:
            buff = await self.transport.read_bytes(1)
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

    async def recv_mqtt_packet(self) -> Awaitable[Packet]:
        # read packet type & flags (fixed header first byte)
        pktype, flags = await self.read_pktype_flags()
#       logging.info(f"pktype: {pktype} flags: {flags: 02X}")
        self.received_bytes += 1 
        if not pktype in self.handlers:
            logging.error(f"Invalid packet type: {pktype}")
            return None
        
        pktype = PacketType(pktype)
        if self.state != State.CONNECTED and pktype!=PacketType.CONNECT:
            logging.error(f"Error state:{self.state} remote ip:{self.remote_ip}")
            return None

        # read remaining lenght
        remain_len = await self.read_remaining_length()
        if remain_len is None:
            logging.error("Invalid remaining length")
            return None
        
        # read remaining data    
        data = await self.transport.read_bytes(remain_len)
        self.received_bytes += remain_len 
        # unpack remaining data
        packet = PacketClass.get(pktype)(ver=self.protocol_version)
        packet.set_flags(flags)
        reader = BytesIO(data)
        if not packet.unpack(reader):
            packet = None
        reader.close()
        return packet

    async def start_serving(self) -> Awaitable[None]:
        logging.info(f"TCP connecting from {self.remote_ip}")
        IOLoop.current().spawn_callback(self.connect_timout)
        while True:
            try:
                packet = await self.recv_mqtt_packet()
                self.last_timestamp = time.time()
                if packet:
                  # logging.info(f'packet version: {packet.version}')
                    await self.handle_packet(packet)
                else:
                    if self.state == State.CONNECTED and self.protocol_version==protocol.MQTT50:
                        await self.disconnect(Reason.MalformedPacket)
                    self.transport.close()
            except TransportClosedError:
                logging.error(f"remote: {self.remote_ip} be closed")
                await self.closed_handler()
                break
            
    async def handle_packet(self, packet: Packet) -> Awaitable[None]:
        handler = self.handlers[packet.get_type()]
        await handler(packet)

    async def connack_handler(self, packet: Connack) -> Awaitable[None]:
        if self.state != State.CONNECTING:
            logging.error(f"Error state:{self.state} remote ip:{self.remote_ip}")
            self.transport.close()            
            return
        ver = packet.get_version()
        if ver != protocol.MQTT50:
            logging.error(f"Error MQTT version:{ver}  remote ip:{self.remote_ip}")
            self.transport.close()            
            return
        rcode = packet.reason_code()
        if rcode != Reason.Success:
            logging.error(f"Error ConnAck Reason: {rcode.name}  remote ip:{self.remote_ip}")
            self.transport.close()            
            return
        from .memdb import MemDB
        self.app = MemDB.instance().getApp(self.appid)
        logging.info(f"R CONNACK {packet.clientid}")
        self.state = State.CONNECTED
        return

    async def connect(self, ack_flags: int, rcode: Reason) -> Awaitable[None]:
        self.state = State.CONNECTING
        packet = Connect(protocol.MQTT50)
        packet.set_username("bridge@mqtt")
        packet.set_password(self.token)
        packet.set_clientId(self.nodeid)
        packet.set_keep_alive(20)
        packet.set_clean_start(False)
        self.connect = packet
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S CONNECT {self.connect.clientid}")

    async def disconnect(self, rcode: Reason) -> Awaitable[None]:
        packet = Disconnect(self.protocol_version)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
            packet.set_reason_string(rcode.name)
            data = packet.full_pack()
            await self.transport.write(data)
        self.state = State.DISCONNECTED_BY_SERVER
        self.transport.close()
        logging.info(f"S DISCONNECT client_id:{self.connect.clientid}")

    async def publish_handler(self, packet: Publish) -> Awaitable[None]:
        qos = packet.get_qos()
        pid = packet.get_pid()
        topic = packet.topic
        retain = int(packet.get_retain())
        dup = int (packet.get_dup()) 
        clientid = self.connect.clientid
        logging.info(f"R PUBLISH {topic} (d{dup} q{qos} r{retain} m{pid}) {clientid}")
        
        if qos==QoS.qos0 and dup:
            if self.protocol_version == protocol.MQTT50:
                await self.disconnect(Reason.ProtocolError)
            else:
                self.state = State.DISCONNECTED_BY_SERVER
            self.transport.close()
            logging.error("Connection be closed. Reason: d{dup} q{qos}")
            return
        
        if not self.verifyTopic(topic):
            if self.protocol_version == protocol.MQTT50:
                await self.disconnect(Reason.InvalidTopicName)
            else:
                self.state = State.DISCONNECTED_BY_SERVER
            self.transport.close()
            logging.error("Connection be closed. Reason: InvalidTopicName")
            return

        # handle topic alias
        if self.protocol_version==protocol.MQTT50:
            packet.propset.delete(Property.Subscription_Identifier)
            alias = packet.topic_alias()
            if not alias is None:
                if alias == 0 or alias > Config.topic_alias_maximum:
                    logging.error(f"Invalid topic alias:{alias} topic:{topic}")
                    await self.disconnect(Reason.InvalidTopicAlias)
                    return
                if topic:
                    self.alias2topic_map[alias] = topic
                elif alias in self.alias2topic_map:
                    topic = self.alias2topic_map[alias]
                    packet.set_topic(topic)
                else:                
                    logging.error(f"Protocol error topic alias:{alias} not in map")
                    await self.disconnect(Reason.ProtocolError)
                    return
                
        rcode = Reason.Success
        if qos > 0 and not dup:
            if self.receive_quota == 0:
                rcode = Reason.QuotaExceeded
                logging.warning(f"warning: QuotaExceeded {self.connect.receive_maximum()}")
            else:
                self.receive_quota -= 1
        if qos == QoS.qos1:
            await self.puback(pid, rcode)
            self.receive_quota += 1
        elif qos == QoS.qos2:
            if pid not in self.app.getSession(clientid).incoming_inflight:
                self.app.getSession(clientid).add_incoming_inflight_message(packet)
            await self.pubrec(pid, rcode)

        packet.from_clientid = clientid
        payload = packet.payload
        if retain :
            if payload:
                self.app.storeRetainMsg(packet)
                await self.app.dispatch(packet)
            else:
                self.app.removeRetainMsg(packet)
        else:
            await self.app.dispatch(packet)

    async def puback(self, pid: PacketID, rcode: Reason) -> Awaitable[None]:
        packet = Puback(self.protocol_version)
        packet.set_pid(pid)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S PUBACK (m{pid}) {self.connect.clientid}")
        
    async def pubrec(self, pid: PacketID, rcode: Reason) -> Awaitable[None]:
        packet = Pubrec(self.protocol_version)
        packet.set_pid(pid)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S PUBREC (m{pid}) {self.connect.clientid}")

    async def pubrel(self, pid: PacketID, rcode: Reason) -> Awaitable[None]:
        packet = Pubrel(self.protocol_version)
        packet.set_pid(pid)
        self.app.getSession(self.connect.clientid).add_outgoing_inflight_message(packet)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S PUBREL (m{pid}) {self.connect.clientid}")

    async def pubcomp(self, pid: PacketID, rcode: Reason) -> Awaitable[None]:
        packet = Pubcomp(self.protocol_version)
        packet.set_pid(pid)
        if self.protocol_version == protocol.MQTT50:
            packet.set_reason_code(rcode)
        data = packet.full_pack()
        await self.transport.write(data)

        logging.info(f"S PUBCOMP (m{pid}) {self.connect.clientid}")

    async def puback_handler(self, packet: Puback) -> Awaitable[None]:
        pid = packet.get_pid()
        clientid = self.connect.clientid
        logging.info(f"R PUBACK (m{pid}) {clientid}")
        if not self.app.getSession(clientid).verify_outgoing_inflight_message(pid, PacketType.PUBLISH):
            await self.disconnect(Reason.ProtocolError)
            logging.error("Not expected PUBACK packet")
            return
        self.app.getSession(clientid).remove_outgoing_inflight_message(pid)

    async def pubrec_handler(self, packet: Pubrec) -> Awaitable[None]:
        pid = packet.get_pid()
        clientid = self.connect.clientid
        logging.info(f"R PUBREC (m{pid}) {clientid}")
        if not self.app.getSession(clientid).verify_outgoing_inflight_message(pid, PacketType.PUBLISH):
            await self.disconnect(Reason.ProtocolError)
            logging.error("Not expected PUBREC packet")
            return
        await self.pubrel(pid, Reason.Success)

    async def pubrel_handler(self, packet: Pubrel) -> Awaitable[None]:
        pid = packet.get_pid()
        clientid = self.connect.clientid
        logging.info(f"R PUBREL (m{pid}) {clientid}")
        if not self.app.getSession(clientid).verify_incoming_inflight_message(pid, PacketType.PUBLISH):
            await self.disconnect(Reason.ProtocolError)
            logging.error("Not expected PUBREL packet")
            return
        self.app.getSession(clientid).remove_incoming_inflight_message(pid)
        await self.pubcomp(pid, Reason.Success)

    async def pubcomp_handler(self, packet: Pubcomp) -> Awaitable[None]:
        pid = packet.get_pid()
        clientid = self.connect.clientid
        logging.info(f"R PUBCOMP (m{pid}) {clientid}")
        if not self.app.getSession(clientid).verify_outgoing_inflight_message(pid, PacketType.PUBREL):
            await self.disconnect(Reason.ProtocolError)
            logging.error("Not expected PUBREC packet")
            return
        self.app.getSession(clientid).remove_outgoing_inflight_message(pid)

    async def suback(self, pid: PacketID, rcodes: List[Reason]) -> Awaitable[None]:
        packet = Suback(self.protocol_version, rcodes)
        packet.set_pid(pid)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S SUBACK (m{pid}) {self.connect.clientid}")

    async def unsuback(self, pid: PacketID, rcodes: List[Reason]) -> Awaitable[None]:
        packet = Unsuback(self.protocol_version, rcodes)
        packet.set_pid(pid)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S UNSUBACK (m{pid}) {self.connect.clientid}")

    async def subscribe_handler(self, packet: Subscribe) -> Awaitable[None]:
        clientid = self.connect.clientid
        logging.info(f"R SUBSCRIBE (m{packet.pid}) {clientid}")
        rcodes = list()
        for top in packet.topicOpsList:
            tf = top.topic_filter
            if self.verifyTopicFilter(tf):
                if SharedTopicRegexp.match(tf) and top.NL():
                    await self.disconnect(Reason.ProtocolError)
                    logging.error(f"Error share subscription with NL flag TF:{tf} options:{top.options:02X}")
                    return
                rcodes.append(top.QoS())
                top.valid = True
                self.app.addSubscription(tf, top, self.connect.clientid)
            else:
                rcodes.append(Reason.InvalidTopicFilter)
                top.valid = False
        pid = packet.get_pid()
        await self.suback(pid, rcodes)
        await self.app.dispatchRetainMessages(packet, clientid)

    async def unsubscribe_handler(self, packet: Unsubscribe) -> Awaitable[None]:
        rcodes = list()
        for tf in packet.topic_filter_list:
            if self.verifyTopicFilter(tf):
                rcodes.append(Reason.Success)
                self.app.delSubscription(tf, self.connect.clientid)
            else:
                rcodes.append(Reason.InvalidTopicFilter)
        pid = packet.get_pid()
        clientid = self.connect.clientid
        logging.info(f"R UNSUBSCRIBE (m{pid}) {clientid}")
        await self.unsuback(pid, rcodes)

    async def pingresp(self) -> Awaitable[None]:
        packet = Pingresp(self.protocol_version)
        data = packet.full_pack()
        await self.transport.write(data)
        logging.info(f"S PINGRESP {self.connect.clientid}")

    async def pingreq_handler(self, packet: Pingreq) -> Awaitable[None]:
        logging.info(f"R PINGREQ  {self.connect.clientid}")
        await self.pingresp()

    async def disconnect_handler(self, packet: Disconnect) -> Awaitable[None]:
        sei = packet.session_expiry_interval()
        sei0 = self.connect.session_expiry_interval()
        self.disconnect_rcode = packet.rcode
        if (self.state != State.CONNECTED) or (sei0==0 and sei>0):
            logging.error(f"Error state:{self.state} remote ip:{self.remote_ip}")
            if self.protocol_version == protocol.MQTT50:
                await self.disconnect(Reason.ProtocolError)
            logging.error(f"Connection be closed. reason: ProtocolError")
            return
        
        logging.info(f"R DISCONNECT {self.connect.clientid}")
        session = self.app.getSession(self.connect.clientid)
        if session:
            session.sei = sei

        self.state = State.DISCONNECTED_BY_CLIENT
        if self.protocol_version == protocol.MQTT50 and packet.rcode==Reason.DisconnectWithWillMessage:
            await self.deliveryWillMsg()
        self.transport.close()

    async def deliveryWillMsg(self) -> Awaitable[None]:
        if not self.connect.will:
            return
        packet = Publish(ver=self.protocol_version)
        packet.set_topic(self.connect.will_topic)
        packet.set_qos(self.connect.will_qos)
        packet.set_retain(self.connect.will_retain)
        packet.payload = self.connect.will_message
        packet.propset = self.connect.willpropset
        
        will_delay_interval = self.connect.willpropset.get(Property.Will_Delay_Interval)
        if will_delay_interval:
            await gen.sleep(will_delay_interval)

        if self.connect.will_retain:
            self.app.storeRetainMsg(packet)

        mei = self.connect.willpropset.get(Property.Message_Expiry_Interval)
        mei = mei if mei else Config.message_expiry_interval
        packet.expire_at = time.time() + mei 

        logging.info(f"Will Message topic: {self.connect.will_topic} qos: {self.connect.will_qos}")
        await self.app.dispatch(packet)

    async def auth_handler(self, packet: Auth) -> Awaitable[None]:
        await self.disconnect(Reason.ImplementationSpecificError)
        self.transport.close()
        logging.info(f"R AUTH {self.connect.clientid}, but not implimented")

    async def closed_handler(self) -> Awaitable[None]:
        if self.state == State.CONNECTED:
            self.state = State.CLOSED
            await self.deliveryWillMsg()
        elif self.state==State.INITIATED:
            return 
        logging.debug(f'state: {self.state.name}')
        if self.state==State.KICKOUT or self.state==State.DISCONNECTED_BY_CLIENT:
            self.app.delSession(self.connect.clientid)
        elif self.state==State.CLOSED:
            if self.connect.get_version()==protocol.MQTT311:
                sei = self.app.sei
                await self.session_expired(sei)
            if self.connect.get_version()==protocol.MQTT50:
                sei = self.connect.propset.get(Property.Session_Expiry_Interval)
                sei = 0 if sei is None else sei
                sei = min(sei, self.app.sei)
                if sei >0 :
                    await self.session_expired(sei)
                else:
                    self.app.delSession(self.connect.clientid)

    async def connect_timout(self) -> Awaitable[None]:
        await gen.sleep(INIT_INTERVAL)
        if self.state == State.INITIATED:
            logging.error(f"CONNECT TIMEOUT ip: {self.remote_ip}")
            self.transport.close()

    async def keep_alive_timeout(self) -> Awaitable[None]:
        duration = self.keep_alive * FACTOR
        while self.state == State.CONNECTED:
            await gen.sleep(duration)
            cur_timestamp = time.time()
            if self.state == State.CONNECTED and cur_timestamp - self.last_timestamp > duration:
                logging.info(f"TIMEOUT: clientID: {self.connect.clientid} ip: {self.remote_ip}")
                self.transport.close()
                return

    async def session_expired(self, sei: int) -> Awaitable[None]:
        self.state = State.WAITING_EXPIRED
        await gen.sleep(sei)
        session = self.app.getSession(self.connect.clientid)
        if session and session.waiter.state==State.WAITING_EXPIRED:
            self.state = State.EXPIRED
            self.app.delSession(self.connect.clientid)
            logging.info(f"Session expired clientID: {self.connect.clientid}")
        else:
            logging.info(f"clientID: {self.connect.clientid} reconnected")
