# -*- coding: utf-8 -*-
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved

import os
import time
import re
import logging
import struct
from io import BytesIO

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError

from .MqttMemDB import MqttMemDB
from .MqttError import MqttError
from .MqttAuthenticate import MqttAuthenticate
from .MqttPush2Clients import pub4pub, pub4sub

from ..core.MqttMessageBase import MqttMessageBase
from ..core.MqttMessageFactory import MqttMessageFactory
from ..core.MqttException import MqttException
from ..core.MqttConnect import MqttConnect
from ..core.MqttConnAck import MqttConnAck
from ..core.MqttDisconnect import MqttDisconnect
from ..core.MqttPingReq import MqttPingReq
from ..core.MqttPingResp import MqttPingResp
from ..core.MqttPublish import MqttPublish
from ..core.MqttPubAck import MqttPubAck
from ..core.MqttPubRec import MqttPubRec
from ..core.MqttPubRel import MqttPubRel
from ..core.MqttPubComp import MqttPubComp
from ..core.MqttSubscribe import MqttSubscribe
from ..core.MqttSubAck import MqttSubAck
from ..core.MqttUnsubscribe import MqttUnsubscribe
from ..core.MqttUnsubAck import MqttUnsubAck

class MqttContext(object):
    INITIATED       = 0
    CONNECTING      = 1
    CONNECTED       = 2    
    DISCONNECTING   = 3
    DISCONNECTED    = 4
    KICKOUT         = 5
    CLOSING_FOR_EXCEPTION = 6
    KEEP_ALIVE_TIMEOUT = 7
    CLOSED = 8
    # FACTOR = 1.5
    FACTOR = 1.382

    def __init__(self, stream, address):
        self.state = MqttContext.INITIATED
        self.mem_db = MqttMemDB.instance()
        self.mqtt_connect = None
        self.mqtt_session = None
        self.pub_acl = None
        self.sub_acl = None
        self.keep_alive = 60
        self.auth = MqttAuthenticate()
        self.last_timestamp = time.time()
        self.stream = stream
        self.remote_ip = address
        self.received_bytes = 0

        self.handlers = {
            MqttMessageBase.MESSAGE_TYPE_CONNECT:       self.connect_handler,
            MqttMessageBase.MESSAGE_TYPE_PUBLISH:       self.publish_handler,
            MqttMessageBase.MESSAGE_TYPE_PUBACK:        self.puback_handler,
            MqttMessageBase.MESSAGE_TYPE_PUBREC:        self.pubrec_handler,
            MqttMessageBase.MESSAGE_TYPE_PUBREL:        self.pubrel_handler,
            MqttMessageBase.MESSAGE_TYPE_PUBCOMP:       self.pubcomp_handler,
            MqttMessageBase.MESSAGE_TYPE_SUBSCRIBE:     self.subscribe_handler,
            MqttMessageBase.MESSAGE_TYPE_UNSUBSCRIBE:   self.unsubscribe_handler,
            MqttMessageBase.MESSAGE_TYPE_PINGREQ:       self.pingreq_handler,
            MqttMessageBase.MESSAGE_TYPE_DISCONNECT:    self.disconnect_handler,
        }

    async def recv_mqtt_packet(self):
        result = None
        """
            read mqtt message type
        """
        data = await self.stream.read_bytes(1)
        b, = struct.unpack("!B", data)
        msgtype = b >> 4
        packet = bytearray()
        packet.extend(data)

        """
            read remain len of mqtt packet
        """
        bytes_of_len = 0
        remain_len_packet = bytearray()

        """
            bytes_of_len must be less or eq. 4 bytes
        """
        is_valid_len = False
        while bytes_of_len < 4:
            data = await self.stream.read_bytes(1)
            bytes_of_len += 1
            remain_len_packet.extend(data)
            b, = struct.unpack("!B", data)
            if (b & 0x80):
                continue
            else:
                is_valid_len = True
                break

        if not is_valid_len:
            logging.error("msgtype(%d) %s  ip %s" % (msgtype, "Invalid Mqtt packet length", self.remote_ip))
        else:
            """
                read reamin data of mqtt packet
            """
            packet.extend(remain_len_packet)
            inputstream = BytesIO(remain_len_packet)
            remain_len = MqttMessageBase.decodeRemainLenFromMbi(inputstream)
            inputstream.close()
            data = await self.stream.read_bytes(remain_len)
            packet.extend(data)
            result = bytes(packet)
        return result

    async def start_loop(self):
        logging.info("TCP connecting from: " +str(self.remote_ip))
        while True:
            try:
                data = await self.recv_mqtt_packet()
                if data:
                    self.received_bytes += len(data)
                    await self.packet_handler(data)
                else:
                   stream.close()
            except StreamClosedError:
                await self.closed_handler()
                self.state = MqttContext.CLOSED
                logging.error("%s be closed.", self.remote_ip)
                break

    async def packet_handler(self, packet):
        try:
            mqtt_message = MqttMessageFactory.createMqttMessage(packet)
            msgtype = mqtt_message.getType()
            self.last_timestamp = time.time()
            if not msgtype in self.handlers:
                raise MqttException(0, MqttException.REASON_CODE_INVALID_PACKET)
            else:
                message_handler = self.handlers[msgtype]
                result = await message_handler(mqtt_message)
                if result != MqttError.SUCCESS:
                    logging.info("handler result: %d" % result)
                    raise MqttException(0, MqttException.REASON_CODE_INVALID_PACKET)
        except Exception as e:
            logging.info("MqttContext state: %d" % self.state)
            logging.exception(repr(e))
            '''
                to close tcp/ip connection
            '''
            self.state = MqttContext.CLOSING_FOR_EXCEPTION
            self.stream.close()
        finally:
            pass

    async def connect_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if not isinstance(mqtt_message, MqttConnect):
            logging.error("state(%d): %s ip %s" % (msgtype, "Not CONNCET packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        if self.state != MqttContext.INITIATED:
            logging.error("state(%d): %s ip %s" % (self.state, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR
            
        self.state = MqttContext.CONNECTING
        self.mqtt_connect = mqtt_message
        
        client_id = mqtt_message.getClientId()
        user_name = mqtt_message.getUserName()
        password = mqtt_message.getUserPassword()
        clean_session = mqtt_message.isCleanSession()
        keep_alive_interval = mqtt_message.getKeepAliveInterval()
        ack_code =  self.auth.auth(client_id, user_name, password)
        ack_flags = 0x00
        logging.info("CONNECT recv [ client_id: %s clean_session: %s keep_alive_interval: %d ack_code: %d ]" % (client_id, clean_session, keep_alive_interval, ack_code))
        if ack_code == MqttException.REASON_CODE_CLIENT_ACCEPTED:
            self.pub_acl = self.auth.pub_acl_list(client_id)
            self.sub_acl = self.auth.sub_acl_list(client_id)
            self.state = MqttContext.CONNECTED
            if self.mem_db.session_present(client_id):
                if not clean_session:
                    ack_flags = 0x01
                session = self.mem_db.get_session(client_id)
                logging.error("session is present: {}".format(client_id))
                if session.isActived():
                    context = self.mem_db.get_session(client_id).context
                    context.state = MqttContext.KICKOUT
                    logging.error(" KICKOUT: client_id (%s) ip %s" % (client_id, context.remote_ip))
                    context.stream.close()
            context = self
            self.mem_db.add_session(context)
            keep_alive = mqtt_message.getKeepAliveInterval()
            if keep_alive:
                self.keep_alive = keep_alive
            IOLoop.current().spawn_callback(self.monitor_timeout)
            await self.send_connack(ack_flags, ack_code)
            return MqttError.SUCCESS
        else:
            self.stream.close()
            return MqttError.DENY_CONNECT

    async def publish_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        if not isinstance(mqtt_message, MqttPublish):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PUBLISH packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        qos = mqtt_message.getQos()
        pid = mqtt_message.getPid()
        topic = mqtt_message.getTopic()
        client_id = self.mqtt_connect.getClientId()
        logging.info("PUBLISH recv [pid: %d qos: %d topic: %s retain: %s client_id: %s]" % (pid, qos, topic, mqtt_message.isRetain(), client_id))
        logging.info("payload: %s " % (mqtt_message.getPayload()))

        if not self.verify_pub_topic(topic):
            logging.error("topic(%s): %s ip %s" % (topic, "Invalid PUBLISH topic", self.remote_ip))
            return MqttError.INVALID_PACKET

        if qos == 1:
            await self.send_puback(pid)
        elif qos == 2:
            await self.send_pubrec(pid)
        
        if qos==2:
            if self.mqtt_session.isAlreadIncomingInflightMessage(pid):
                return MqttError.SUCCESS
            else:
                self.mqtt_session.add_incoming_inflight_message(mqtt_message)
                self.mem_db.statistic.inc_in_flight_i()

        if mqtt_message.getPayload():
            if mqtt_message.isRetain():
                if self.mqtt_session.isPresentRetainedTopic(topic) or self.mqtt_session.getRetainedTopicCount() < 3:
                    self.mem_db.add_pub(mqtt_message)
                    self.mqtt_session.add_retain_pub(topic)
                    await pub4pub(mqtt_message, self.mem_db)
                else:
                    logging.error("topic(%s): %s ip %s" % (topic, " retain topic count > 3", self.remote_ip))
                    return MqttError.INVALID_PACKET
            else:
                await pub4pub(mqtt_message, self.mem_db)
                
        elif mqtt_message.isRetain():
            self.mem_db.unpub(mqtt_message)

        self.mem_db.statistic.inc_recv_pub()

        return MqttError.SUCCESS

    async def puback_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR
        client_id = self.mqtt_connect.getClientId()
        if not isinstance(mqtt_message, MqttPubAck):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PUBACK packet", self.remote_ip))
            return MqttError.INVALID_PACKET
        pid = mqtt_message.getPid()
        if not self.mqtt_session.verifyOutgoingInflightMessage(pid, MqttMessageBase.MESSAGE_TYPE_PUBLISH):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Invalid PUBACK packet", self.remote_ip))
            return MqttError.INVALID_PACKET
        logging.info("PUBACK recv [pid: %d client_id: %s]" % (pid, client_id))
        self.mqtt_session.remove_outgoing_inflight_message(pid)
        self.mem_db.statistic.inc_sent_pub()

        return MqttError.SUCCESS
    
    async def pubrec_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        client_id = self.mqtt_connect.getClientId()
        if not isinstance(mqtt_message, MqttPubRec):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PUBREC packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        pid = mqtt_message.getPid()
        if not self.mqtt_session.verifyOutgoingInflightMessage(pid, MqttMessageBase.MESSAGE_TYPE_PUBLISH):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Invalid PUBREC packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        logging.info("PUBREC recv [pid: %d client_id: %s]" % (pid, client_id))
        await self.send_pubrel(pid)
        return MqttError.SUCCESS
    
    async def pubrel_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        client_id = self.mqtt_connect.getClientId()
        if not isinstance(mqtt_message, MqttPubRel):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PUBREL packet", self.remote_ip))
            return MqttError.INVALID_PACKET
        
        pid = mqtt_message.getPid()
        if not self.mqtt_session.verifyIncomingInflightMessage(pid, MqttMessageBase.MESSAGE_TYPE_PUBLISH):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Invalid PUBREL packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        logging.info("PUBREL recv [pid: %d client_id: %s]" % (pid, client_id))

        await self.send_pubcomp(pid)
        self.mqtt_session.remove_incoming_inflight_message(pid)

        return MqttError.SUCCESS
        
    async def pubcomp_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        client_id = self.mqtt_connect.getClientId()
        
        if not isinstance(mqtt_message, MqttPubComp):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PUBCOMP packet", self.remote_ip))
            return MqttError.INVALID_PACKET
       
        pid = mqtt_message.getPid()
        if not self.mqtt_session.verifyOutgoingInflightMessage(pid, MqttMessageBase.MESSAGE_TYPE_PUBREL):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Invalid PUBCOMP packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        logging.info("PUBCOMP recv [pid: %d client_id: %s]" % (pid, client_id))
        
        self.mqtt_session.remove_outgoing_inflight_message(pid)
        self.mem_db.statistic.inc_sent_pub()
        return MqttError.SUCCESS

    
    async def subscribe_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        if not isinstance(mqtt_message, MqttSubscribe):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not SUBSCRIBE packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        client_id = self.mqtt_connect.getClientId()
        pid = mqtt_message.getPid()
        logging.info("SUBSCRIBE recv [pid: %d client_id: %s]" % (pid, client_id))
        logging.info("sub_list: %s " % (mqtt_message.sub_list))
        await self.send_suback(mqtt_message)
        self.mem_db.add_sub(client_id, mqtt_message)

        """
        await pub4sub(mqtt_message, self.mem_db, client_id)
        """
        return MqttError.SUCCESS
    
    async def unsubscribe_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR

        if not isinstance(mqtt_message, MqttUnsubscribe):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not UNSUBSCRIBE packet", self.remote_ip))
            return MqttError.INVALID_PACKET
        
        client_id = self.mqtt_connect.getClientId()
        pid = mqtt_message.getPid()

        logging.info("UNSUBSCRIBE recv [pid: %d client_id: %s]" % (pid, client_id))
        logging.info("unsub_list: %s " % (mqtt_message.unsub_list))
        await self.send_unsuback(pid)
        self.mem_db.unsub(client_id, mqtt_message)

        return MqttError.SUCCESS
    
    async def pingreq_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR
        client_id = self.mqtt_connect.getClientId()
        if not isinstance(mqtt_message, MqttPingReq):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PING packet", self.remote_ip))
            return MqttError.INVALID_PACKET
        logging.info("PINGREQ recv [client_id: %s]" % (client_id))
        await self.send_pingresp()
        return MqttError.SUCCESS
    
    async def disconnect_handler(self, mqtt_message):
        msgtype = mqtt_message.getType()
        if self.state != MqttContext.CONNECTED:
            logging.error("state(%d): %s ip %s" % (msgtype, "Invalid Mqtt session state", self.remote_ip))
            return MqttError.SESSION_STATE_ERR
        
        if not isinstance(mqtt_message, MqttDisconnect):
            logging.error("msgtype(%d) %s ip %s" % (msgtype, "Not PING packet", self.remote_ip))
            return MqttError.INVALID_PACKET

        client_id = self.mqtt_connect.getClientId()
        logging.info("DISCONNECT recv [client_id: %s]" % (client_id))
        self.state = MqttContext.DISCONNECTING
        self.mem_db.remove_session (self)
        return MqttError.SUCCESS
        
    async def closed_handler(self):
        if self.state == MqttContext.DISCONNECTING:
            self.state = MqttContext.DISCONNECTED
        elif self.state == MqttContext.CONNECTED:
            if self.mqtt_connect.hasWill():
                (retain, topic, payload, qos) =  self.mqtt_connect.getWillInfo()
                mqtt_pub = MqttPublish(0, False, qos, topic, payload, retain)
                if retain:
                    self.mem_db.add_pub (mqtt_pub)
                await pub4pub(mqtt_pub, self.mem_db)
            client_id = self.mqtt_connect.getClientId()
            self.mem_db.setSessionActived(client_id,False)
            self.state = MqttContext.CLOSED

    async def send_connack(self, ack_flags, connack_code):
        mqtt_message = MqttConnAck(ack_flags, connack_code)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("CONNACK sent [client_id: %s]" % (client_id))

    async def send_puback(self, pid):
        mqtt_message = MqttPubAck()
        mqtt_message.setPid(pid)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("PUBACK sent [pid: %d client_id: %s]" % (pid, client_id))
        
    async def send_pubrec(self, pid):
        mqtt_message = MqttPubRec()
        mqtt_message.setPid(pid)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("PUBREC sent [pid: %d client_id: %s]" % (pid, client_id))

    async def send_pubrel(self, pid):
        mqtt_message = MqttPubRel()
        mqtt_message.setPid(pid)
        data = mqtt_message.pack()
        await self.stream.write(data)
        self.mqtt_session.add_outgoing_inflight_message(mqtt_message)
        client_id = self.mqtt_connect.getClientId()
        logging.info("PUBREL sent [pid: %d client_id: %s]" % (pid, client_id))
 
    async def send_pubcomp(self, pid):
        mqtt_message = MqttPubComp()
        mqtt_message.setPid(pid)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("PUBCOMP sent [pid: %d client_id: %s]" % (pid, client_id))
        
    async def send_suback(self, mqtt_sub):
        i = 0
        for topic, qos in mqtt_sub.sub_list:
            if not self.verify_sub_topic(topic):
                mqtt_sub.sub_list[i] = (topic, 0x80) 
            i += 1
        mqtt_message = MqttSubAck(mqtt_sub)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        pid = mqtt_sub.getPid()
        logging.info("SUBACK sent [pid: %d client_id: %s]" % (pid, client_id))
    
    async def send_unsuback(self, pid):
        mqtt_message = MqttUnsubAck()
        mqtt_message.setPid(pid)
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("UNSUBACK sent [pid: %d client_id: %s]" % (pid, client_id))

    async def send_pingresp(self):
        mqtt_message = MqttPingResp()
        data = mqtt_message.pack()
        await self.stream.write(data)
        client_id = self.mqtt_connect.getClientId()
        logging.info("PINGRESP sent [client_id: %s]" % (client_id))

    async def monitor_timeout(self):
        duration = self.keep_alive * MqttContext.FACTOR
        while self.state == MqttContext.CONNECTED:
            await gen.sleep(duration)
            cur_timestamp = time.time()
            if self.state == MqttContext.CONNECTED and cur_timestamp - self.last_timestamp > duration:
                client_id = self.mqtt_connect.getClientId()
                logging.error("TIMEOUT: client_id (%s) ip %s" % (client_id, self.remote_ip))
                self.stream.close()

    def verify_sub_topic(self, topic):
        if len(topic)==0:
            return False
        if topic[0]=='/':
            return False
        if topic.count('#')>1:
            return False
        if topic.count('+')>1:
            return False
        if topic.count('#')==1 and topic.count('+')==1:
            return False
        if '#' in topic and topic[-1] != '#':
            return False
        splited_topic =  topic.split('/')
        if not len(splited_topic) in [3, 4]:
            return False
        if '+' in splited_topic and splited_topic[1] != '+':
            return False
        for item in splited_topic:
            if '+' in item and len(item) != 1:
                return False
            if '#' in item and len(item) != 1:
                return False
        return self._acl_check(topic, self.sub_acl)

    def verify_pub_topic(self, topic):
        if len(topic)==0:
            return False
        if topic[0]=='/':
            return False
        if '#' in topic or '+' in topic: 
            return False
        return self._acl_check(topic, self.pub_acl)

    def _acl_check(self, topic, acl):
        result = False
        for acl_topic in acl:
            if '#' in acl_topic or '+' in acl_topic:
                pattern = re.compile(acl_topic.replace('#', '.*').replace('$', '\\$').replace('+', '[-\\+\\$\\s\\w\\d]+'))
                match_obj = pattern.match(topic)
                if match_obj:
                    result = True
                    break
            else:
                pattern = re.compile(topic)
                match_obj = pattern.match(acl_topic)
                if match_obj:
                    result = True
                    break
        return result
