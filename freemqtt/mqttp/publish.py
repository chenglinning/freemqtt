# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import time
import logging
from site import venv
from .packet import Packet
from .pktype import PacketType, QoS
from .property import PropertSet, Property
from . import protocol, utils
from ..server.config import Config

class Publish(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Publish, self).__init__(ver, PacketType.PUBLISH)
        self.topic = None
        self.payload = bytes()
        self.expire_at = None
        self.propset = PropertSet(PacketType.PUBLISH)
        self.from_clientid = None
        self.sharing = False

    def expired_interval(self) -> int:
        ep = self.propset.get(Property.Message_Expiry_Interval)
        if not ep:
            return Config.message_expiry_interval
        return ep

    def set_expired_interval(self, val: int) -> bool:
        return self.propset.set(Property.Message_Expiry_Interval, val)

    def topic_alias(self) -> int:
        return self.propset.get(Property.Topic_Alias)

    def set_topic_alias(self, val: int) -> bool:
        return self.propset.set(Property.Topic_Alias, val)

    def set_topic(self, val: str) -> None:
        self.topic = val
        
    def set_payload(self, val: bytes) -> None:
        self.payload = val

    # unpack connack packet on client side
    def unpack(self, r: io.BytesIO) -> bool:
        if self.qos > QoS.qos2 :
            logging.error(f"Error QoS: {self.qos}")
            return False
        # topic
        topic = utils.read_string(r)
        if self.version==protocol.MQTT311 and not topic:
            logging.error("Error parse topic")
            return False
        if topic:
            if not utils.TopicPublishRegexp.match(topic):
                logging.error(f"Invalid will topic: {topic}")
                return False
        self.topic = topic
	    # packet id
        if self.qos > 0:
            pid = utils.read_int16(r)
            if pid is None:
                logging.error("Error packet ID: None")
                return False
            self.set_pid(pid)

        # properties
        if self.version == protocol.MQTT50:
            if not self.propset.unpack(r):
                logging.error("Error parse properties")
                return False

        # payload
        payload = utils.read_rest_data(r)
        if not payload:
            logging.error("Error parse paylaod")
            return False
        self.payload = payload

        # expire at
        if self.version == protocol.MQTT50:
            self.expire_at = time.time() + self.expired_interval()
        else:
            self.expire_at = time.time() + Config.message_expiry_interval
        return True

    # pack connect packet on client server
    def pack(self) -> bytes:
        w = io.BytesIO()
        # topic
        utils.write_string(w, self.topic)

        # packet id
        if self.qos > 0:
            utils.write_int16(w, self.pid)

        # properties
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)

        # payload
        utils.write_bytes(w, self.payload)
        data = w.getvalue()
        w.close()
        return data
