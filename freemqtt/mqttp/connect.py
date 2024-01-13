# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
import uuid
from .packet import Packet
from . import mask, protocol, utils
from .pktype import PacketType, QoS
from .property import PropertSet, Property, StringPair
from .reason_code import Reason, validReasoneCode


class Connect(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Connect, self).__init__(ver, PacketType.CONNECT)
        self.clientid = None
        self.username = None
        self.password = None
        self.clean_start = False
        self.keep_alive = 60 # default 60 seconds
        self.username_flag = True
        self.password_flag = True

        self.will =  False
        self.will_qos = QoS.qos0
        self.will_retain = False
        self.will_topic = None
        self.will_message = None
        self.propset = PropertSet(PacketType.CONNECT)
        self.willpropset = PropertSet(PacketType.WILLPP)
        self.assigned_id = False
        self.appid = None # application ID, the space is isolated per application of IoT platform

    def receive_maximum(self) -> int:
        rm = self.propset.get(Property.Receive_Maximum)
        return  1024 if rm==None else rm
    
    def maximum_packet_size(self) -> int:
        mx = self.propset.get(Property.Maximum_Packet_Size)
        return 2097152 if mx==None else mx # default 2M bytes
    
    def session_expiry_interval(self) -> int:
        sei = self.propset.get(Property.Session_Expiry_Interval)
        return  sei if sei else 0

    def set_username(self, name: str) -> None:
        self.username = name
        
    def set_password(self, password: str) -> None:
        self.password = password
        
    def set_clientId(self, clientid: str) -> None:
        self.clientid = clientid
        
    def set_clean_start(self, clean: bool) -> None:
        self.clean_start = clean
        
    def set_keep_alive(self, interval: int) -> None:
        self.keep_alive = interval
        
    def set_will(self, will: bool, topic:str=None, message:bytes=None, qos:int=0, retain:bool=False) -> None:
        self.will =  will
        self.will_retain = retain
        self.will_topic = topic
        self.will_message = message
        self.will_qos = qos
        
    def clear_will(self) -> None:
        self.will =  False
        self.will_retain = False
        self.will_topic = None
        self.will_message = None
        self.will_qos = 0

    def conn_flags(self) -> int:
        return self.username_flag << 7 | self.password_flag << 6 | self.will_retain << 5 | self.will_qos << 3 | self.will << 2 | self.clean_start << 1

    def request_response_information(self) -> bool:
        return self.propset.get(Property.Request_Response_Information) == 1
        
    # unpack conncet packet on server side
    def unpack(self, r: io.BytesIO) -> bool:
        proto_name = utils.read_string(r)
        if not proto_name or proto_name != "MQTT":
            logging.error(f"Error protocol name: {proto_name}")
            return False
        proto_ver = utils.read_int8(r)
        if proto_ver != protocol.MQTT311 and proto_ver != protocol.MQTT50:
            logging.error(f"Error protocol version: {proto_ver}")
            return False
        self.set_version(proto_ver)
       
        connect_flags = utils.read_int8(r)
        if connect_flags is None:
            logging.error("Error connect flags: None")
            return False

        # for MQTT V3.1.1 5.0, the bit0 must be 0
        if connect_flags & mask.ConnFlagReserved:
            logging.error(f"Error connect flags: {connect_flags:02X}")
            return False
             
        self.clean_start = (connect_flags & mask.ConnFlagClean) > 0
        self.will =  (connect_flags & mask.ConnFlagWill) > 0
        self.will_qos = (connect_flags & mask.ConnFlagWillQos) >> 3
        self.will_retain = (connect_flags & mask.ConnFlagWillRetain) > 0
        self.username_flag = (connect_flags & mask.ConnFlagUsername) > 0
        self.password_flag = (connect_flags & mask.ConnFlagPassword) > 0
        
        if not self.will and self.will_qos > 0 or self.will_qos > 2:
            logging.error(f"Invalid will QoS: {self.will_qos}")
            return False

        self.keep_alive = utils.read_int16(r)
        if self.keep_alive is None:
            logging.error("Error keep alive interval: None")
            return False

        if proto_ver == protocol.MQTT311:
            if (connect_flags & mask.ConnFlagUsername)==0 and (connect_flags & mask.ConnFlagPassword) > 0:
                logging.error(f"Error connect flags: {connect_flags:02X}")
                return False
        else: # MQTT 5.0
            # connect properties
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
                return False

    	# MQTT3.1.1 5.0  reading client id
        self.clientid = utils.read_string(r)
        if not self.clientid:
            if not self.clean_start:
                return False
            self.clientid = uuid.uuid1().hex[0:8]
            self.assigned_id = True
        
        # Parsing will data
        if self.will:
            # will properties
            if proto_ver==protocol.MQTT50 :
                if not self.willpropset.unpack(r):
                    logging.error("Error parsing will properties")
                    return False
            # will topic
            will_topic = utils.read_string(r)
            if not will_topic:
                logging.error("Error parsing will topic")
                return False
            if not utils.TopicPublishRegexp.match(will_topic):
                logging.error(f"Invalid will topic: {will_topic}")
                return False
            self.will_topic = will_topic

            # will paload
            payload = utils.read_binary_data(r)
            if not payload:
                logging.error(f"Invalid payload: {payload}")
                return False
            self.will_message = payload

        if self.username_flag:
            self.username = utils.read_string(r)
            if not self.username:
                logging.error("Error user name: None")
                return False

        if self.password_flag:
            self.password = utils.read_string(r)
            if not self.password:
                logging.error("Error user password: None")
                return False
                
        return True

    # pack connect packet on client side
    def pack(self) -> bytes:
        w = io.BytesIO()
        utils.write_string(w, protocol.NAME)
        utils.write_int8(w, self.version)
        utils.write_int8(w, self.conn_flags())
        utils.write_int16(w, self.keep_alive)
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)

        utils.write_string(w, self.clientid)

        # pack will data
        if self.will:
            # will properties
            if self.version == protocol.MQTT50 :
                wppdata =  self.willpropset.pack()
                plen = len(wppdata)
                utils.write_uvarint(w, plen)
                utils.write_bytes(w, wppdata)
            # will topic
            utils.write_string(w, self.will_topic)
            # will paload
            utils.write_binary_data(w, self.will_message)

        if self.username_flag:
            utils.write_string(w, self.username)

        if self.password_flag:
            utils.write_string(w, self.password)

        data = w.getvalue()
        w.close()
        return data