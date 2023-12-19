# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from typing import List
from .packet import Packet
from .pktype import PacketType
from .property import PropertSet, Property
from . import protocol, utils, mask
from .reason_code import Reason
class TopicOptPair(object):
    def __init__(self, topic_filter: str, options:int=0, sub_id: int=None) -> None:
        self.topic_filter = topic_filter
        self.options = options
        self.sub_id = sub_id # Subscription Identifier
        self.valid = True
        self.existing = False
        self.shared = False
        
    def QoS(self) -> int:
        return self.options & mask.SubscriptionQoS

    def NL(self) -> bool:
        return self.options & mask.SubscriptionNL != 0
    
    def RAP(self) -> bool:
        return self.options & mask.SubscriptionRAP != 0

    def RH(self) -> int:
        return self.options & mask.SubscriptionRetainHandling >> 4

    def setQoS(self, qos: int) -> None:
        self.options =  (self.options & ~mask.SubscriptionQoS) | qos
        
    def setNL(self, nl:bool) -> None:
        self.options = (self.options & ~mask.SubscriptionNL) | (nl << 2)

    def setRAP(self, rap: bool) -> None:
        self.options = (self.options & ~mask.SubscriptionRAP) | (rap << 3)

    def setRH(self, rh: int) -> None:
        self.options = (self.options & ~mask.SubscriptionRetainHandling) | (rh <<4)

    def subscription_id(self) -> int:
        return self.sub_id

class Subscribe(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Subscribe, self).__init__(ver, PacketType.SUBSCRIBE)
        self.propset = PropertSet(PacketType.SUBSCRIBE)
        self.topicOpsList: List[TopicOptPair] = []

    def valid_SubOpts(self, ops: int) -> bool:
        if self.version == protocol.MQTT311:
            if ops & mask.SubscriptionReservedV3 > 0:
                return False
        if self.version == protocol.MQTT50:
            if ops & mask.SubscriptionReservedV5 > 0:
                return False
            if (ops & mask.SubscriptionRetainHandling) >> 4 == 3:
                return False
        if ops & mask.SubscriptionQoS > 2:
            return False
        return True

    def subscription_id(self) -> int:
        return self.propset.get(Property.Subscription_Identifier)

    # unpack packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x02:
            logging.error(f"Error subscribe flags: {self.flags():02X}")
            return False
        # packet id
        pid = utils.read_int16(r)
        if pid <= 0 :
            logging.error("Error subscribe packet id: None")
            return False
        self.set_pid(pid)
        # properties
        if self.version == protocol.MQTT50 :
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
                return False

        # get subscription id (a int number or None)
        subid = 0
        if self.version == protocol.MQTT50 :
            subid = self.subscription_id()
            if  subid is None:
                pass
            elif subid==0:
                logging.error(f"Error subscription id:{subid}")
                return False
        # topic filter and options pair
        while True:
            topic_filter = utils.read_string(r)
            if not topic_filter:
                break
            logging.info(f"topfic filter: {topic_filter}")
            options = utils.read_int8(r)
            if options is None:
                logging.error("Error subscribe options: None")
                return False
            if self.valid_SubOpts(options):
                self.topicOpsList.append(TopicOptPair(topic_filter, options, subid))
            else:
                logging.error(f"Invalid subscribe options: {options:02X}")
                return False
        # valid payload
        if len(self.topicOpsList) == 0:
            logging.error("No Topic Filter and Subscription Options pair in payload")
            return False
        return True

    # pack packet
    def pack(self) -> bytes:
        w = io.BytesIO()
        # packet id
        utils.write_int16(w, self.pid)
    	# property
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        # payload (topic filter and options pair)
        for pair in self.topicOpsList:
            utils.write_string(w, pair.topic_filter)
            utils.write_int8(w, pair.options)            

        data = w.getvalue()
        w.close()
        return data