# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import re
import time
import logging
from site import venv
from .packet import Packet
from . import mask, pktype, protocol, utils
from .property import PropertSet, Message_Expiry_Interval
from . import reason_code as ReasonCode

class Publish(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Publish, self).__init__(ver, pktype.PUBLISH)
        self.topic = None
        self.payload = bytes()
        self.expire_at = None
        self.propset = PropertSet(pktype.PUBLISH)

    def expired_interval(self) -> int:
        ep = self.propset.get(Message_Expiry_Interval)
        if not ep:
            return 315360000   # 10 years
        return ep

    # unpack connack packet on client side
    def unpack(self, r: io.BytesIO) -> bool:
        if self.qos > protocol.QoS2 :
            logging.error("Error QoS: %d" % self.qos)
            return False

        # topic
        topic = utils.read_string(r)
        if not topic:
            logging.error("Error parsing topic.")
            return False
            
        if not utils.TopicPublishRegexp.match(topic):
            logging.error("Invalid will topic:%s" % topic)
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
#           self.propset = PropertSet(pktype.PUBLISH)
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False

        # payload
        payload = utils.read_rest_data(r)
        if not payload:
            logging.error("Error parsing paylaod.")
            return False
        self.payload = payload

        # expire at
        if self.version  == protocol.MQTT50:
            self.expire_at = time.time() + self.expired_interval()
            pass
        r.close()
        return True

    # pack connect packet on client server
    def pack(self) -> bytes:
        w = io.BytesIO()
        # topic
        utils.write_string(self.topic)

        # packet id
        if self.qos > 0:
            utils.write_int16(r, self.pid)

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
