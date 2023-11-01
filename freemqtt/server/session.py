# -*- coding: utf-8 -*-
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#
import time
import pickle
from typing import Dict

from ..mqttp.packet import Packet
from ..mqttp.connect import Connect
from ..mqttp.subscribe import TopicOptPair

class MQTTSession(object):
    def __init__(self, appid: int, mqttc : Connect) -> None:
        self.sub_dict : Dict[str, TopicOptPair] = {} # { topicfilter : TopicOptPair }
        self.retained_pub_dict : Dict[str, int] = {} # { topic : timestamp }

        # { pid: Packet } for incoming message in-flight
        self.incoming_inflight : Dict[int, Packet] = {}
        
        # { pid: Packet } for outgoing message in-flight
        # Now just allow this dictionary has one element, i.e. only one publish message within outgoing in-flight window  
        self.outgoing_inflight : Dict[int, Packet] = {}

        self.appid = appid
        self.connect = mqttc
        self.active = True
        # current pid
        self.curr_pid = 0

    def clear(self) -> None:
        self.sub_dict.clear()
        self.curr_pid = 0
        self.outgoing_inflight.clear()
        self.incoming_inflight.clear()
        self.retained_pub_dict.clear()

    def next_pid(self) -> int:
        count = 0
        while True:
            self.curr_pid = (self.curr_pid + 1) % 65536
            if self.curr_pid:
                break
        return self.curr_pid

    def is_active(self) -> bool:
        return self.active

    def set_active(self, active: bool) -> None:
        self.active = active

    def get_clientid(self) -> str:
        return self.clientid

    def get_appid(self) -> int:
        return self.appid

    def pickle_dumps(self) -> bytes:
        return pickle.dumps(self)

    def verify_incoming_inflight_message(self, pid : int, pktype : int) -> bool:
        if pid in self.incoming_inflight:
            if self.incoming_inflight[pid].get_type() == pktype:
                return True
        return False

    def verify_outgoing_inflight_message(self, pid : int, pktype : int) -> bool:
        if pid in self.outgoing_inflight:
            if self.outgoing_inflight[pid].get_type() == pktype:
                return True
        return False
    
    def add_incoming_inflight_message(self, packet : Packet) -> None:
        pid = packet.get_pid()
        self.incoming_inflight[pid] = packet
            
    def add_outgoing_inflight_message(self, packet : Packet) -> None:
        pid = packet.get_pid()
        self.outgoing_inflight[pid] = packet
            
    def remove_incoming_inflight_message(self, pid : int) -> None:
        self.incoming_inflight.pop(pid, None)
            
    def remove_outgoing_inflight_message(self, pid : int) -> None:
        self.outgoing_inflight.pop(pid, None)

    def have_received_incoming(self, pid: int) -> bool:
        return pid in self.incoming_inflight

    def add_sub(self, topic: str, qos: int) -> None:
        self.sub_dict[topic] = qos

    def remove_sub(self, topic: str) -> None:
        self.sub_dict.pop(topic, None)

    def get_sub_dict(self) -> Dict(str, int):
        return self.sub_dict

    def clear_sub(self) -> None:
        self.sub_dict.clear()
        
    def set_clean_start(self, clean: bool) -> None:
        self.clean_start = clean

    def is_clean_start(self) -> bool:
        return self.clean_start

    def get_outgoing_inflight_messages(self) -> Dict(int, Packet):
        return self.outgoing_inflight

    def get_outgoing_inflight_message(self, pid) -> Packet:
        return self.outgoing_inflight[pid]

    def is_present_retain_topic(self, topic: str) -> bool:
        return topic in self.retained_pub_dict

    def get_retain_topic_count(self) -> int:
        return len(self.retained_pub_dict)

    def add_retain_pub(self, topic: int) -> None:
        self.retained_pub_dict[topic] = int(time.time())

    def clear_expiried_retain_pub(self):
        pass
