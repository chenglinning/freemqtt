# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from typing import List
from pydoc_data.topics import topics
from .packet import Packet
from . import mask, pktype, protocol, utils
from .property import PropertSet

class Unsubscribe(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Unsubscribe, self).__init__(ver, pktype.UNSUBSCRIBE)
        self.propset = PropertSet(pktype.UNSUBSCRIBE)
        self.topic_filter_list: List[str] = []

    # unpack packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x02:
            logging.error("Error unsubscribe flags: %02X" % self.flags())
            return False
        # packet id
        pid = utils.read_int16(r)
        if pid is None:
            logging.error("Error unsubscribe packet id: None")
            return False
        self.set_pid(pid)
        # properties
        if self.version == protocol.MQTT50 :
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False
        # topic filter
        while True:
            topic_filter = utils.read_string(r)
            if topic_filter is None:
                break
            if utils.TopicFilterRegexp.match(topic_filter):
                self.topic_filter_list.append(topic_filter)
            else:
                logging.error("Invalid topic filter: %s" % topic_filter)
                return False

        # valid payload
        if len(self.topic_filter_list) == 0:
            logging.error("No Topic Filter in payload.")
            return False
        return True

    # pack packet
    def pack(self) -> bytes:
        w = io.BytesIO()
        # packet id
        utils.write_int16(self.pid())
    	# property
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        # payload (topic filter list)
        for topic in self.topic_filter_list:
            utils.write_string(w, topic)
            
        data = w.getvalue()
        w.close()
        return data