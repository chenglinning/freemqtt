# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#
import logging, copy, time
from typing import Dict, Set
from ..mqttp.packet import Packet, PacketType
from ..mqttp.publish import Publish
from ..mqttp.pktype import QoS
from ..mqttp.property import Property
from ..mqttp import protocol

from .waiter import Waiter
from .common import State, SubOption, PacketID, ClientID, AppID, Topic, TopicFilter
class MQTTSession(object):
    def __init__(self, waiter: Waiter) -> None:
        self.waiter = waiter
        self.topicFilterSet : Set[TopicFilter] = set()

        # incoming message in-flight
        self.incoming_inflight : Dict[PacketID, Packet] = {}
        
        # outgoing in-flight window  
        self.outgoing_inflight : Dict[PacketID, Packet] = {}

        # current pid
        self.curr_pid = 0
        # session expire interval
        self.sei = waiter.connect.session_expiry_interval()

        self.curr_alias = 0 # for server side alias

    def clear(self) -> None:
        self.topicFilterSet.clear()
        self.curr_pid = 0
        self.outgoing_inflight.clear()
        self.incoming_inflight.clear()

    def next_pid(self) -> int:
        while True:
            self.curr_pid = (self.curr_pid + 1) % 65536
            if self.curr_pid:
                break
        return self.curr_pid
    
    def next_alias(self) -> int:
        while True:
            self.curr_alias = (self.curr_alias + 1) % self.waiter.alias_maximum
            if self.curr_alias:
                break
        return self.curr_alias

    def online(self) -> bool:
        return self.waiter.state==State.CONNECTED


    def verify_incoming_inflight_message(self, pid: PacketID, pktype: PacketType) -> bool:
        if pid in self.incoming_inflight:
            if self.incoming_inflight[pid].get_type() == pktype:
                return True
        return False

    def verify_outgoing_inflight_message(self, pid: PacketID, pktype: PacketType) -> bool:
        if pid in self.outgoing_inflight:
            if self.outgoing_inflight[pid].get_type() == pktype:
                return True
        return False
    
    def add_incoming_inflight_message(self, packet: Packet) -> None:
        pid = packet.get_pid()
        self.incoming_inflight[pid] = packet
            
    def add_outgoing_inflight_message(self, packet: Packet) -> None:
        pid = packet.get_pid()
        self.outgoing_inflight[pid] = packet
            
    def remove_incoming_inflight_message(self, pid: PacketID) -> None:
        self.incoming_inflight.pop(pid, None)
            
    def remove_outgoing_inflight_message(self, pid: PacketID) -> None:
        self.outgoing_inflight.pop(pid, None)

    def have_received_incoming(self, pid: PacketID) -> bool:
        return pid in self.incoming_inflight

    def add_topic_filter(self, tf: TopicFilter) -> None:
        self.topicFilterSet.add(tf)

    def remove_topic_filter(self, tf: TopicFilter) -> None:
        self.topicFilterSet.discard(tf)

    def get_topic_filter_set(self) -> Set[TopicFilter]:
        return self.topicFilterSet

    def clear_topic_filter_set(self) -> None:
        self.topicFilterSet.clear()
        
    def set_clean_start(self, clean: bool) -> None:
        self.clean_start = clean

    def is_clean_start(self) -> bool:
        return self.clean_start

    def get_outgoing_inflight_messages(self) -> Dict[PacketID, Packet]:
        return self.outgoing_inflight

    def get_outgoing_inflight_message(self, pid: PacketID) -> Packet:
        return self.outgoing_inflight[pid]

    async def delivery(self, packet: Publish, suboption: SubOption, sharing: bool=False) -> bool:
        if self.waiter.protocol_version==protocol.MQTT50 and suboption.NL():
            if packet.from_clientid==self.waiter.connect.clientid:
                return False
        now = time.time()
        if now > packet.expire_at:
            logging.info(f'Expired topic {packet.topic} (q{packet.get_qos()} r{int(packet.get_retain())}) to {self.waiter.connect.clientid}')
            return False
        packet.set_expired_interval(int(packet.expire_at - now))
        packet2 = copy.deepcopy(packet)
        packet2.set_version(self.waiter.protocol_version)
        if not suboption.RAP():
            packet2.set_retain(False)
        packet2.sharing = sharing
        topic = packet2.topic
        qos = min(packet.get_qos(), suboption.QoS())
        dup = int(packet.get_dup())
        pid = int(packet.get_pid())
        retain = int(packet.get_retain())
        packet2.set_qos(qos)
       
        if self.waiter.protocol_version == protocol.MQTT50:
            if topic in self.waiter.topic2alias_map:
                alias = self.waiter.topic2alias_map[topic]
                packet2.set_topic("")
            else:
                alias = self.next_alias()
                self.waiter.topic2alias_map[topic] = alias
            packet2.propset.set(Property.Topic_Alias, alias)
            if suboption.subid:
                packet2.propset.set(Property.Subscription_Identifier, suboption.subid)
                
        if qos==QoS.qos0 and self.waiter.state==State.CONNECTED:
            data = packet2.full_pack()
            await self.waiter.transport.write(data)
            logging.info(f"S PUBLISH {topic} (d{dup} q{qos} r{retain} m{pid}) {self.waiter.connect.clientid} level({packet2.get_version()})")
            return True
       
        pid = self.next_pid()      
        packet2.set_dup(False)
        packet2.set_pid(pid)
        clientid = self.waiter.connect.clientid
        
        packet3 = copy.deepcopy(packet2)
        packet3.set_topic(topic) # restore topic (not "")
        self.add_outgoing_inflight_message(packet3)

        if self.waiter.state==State.CONNECTED and self.waiter.send_quota:
            data = packet2.full_pack()
            self.waiter.send_quota -= 1
            await self.waiter.transport.write(data)
            logging.info(f"S PUBLISH {topic} (d{dup} q{qos} r{retain} m{pid}) {clientid} level({packet2.get_version()})")
            return True
        else:
            logging.info(f"Q PUBLISH {topic} (d{dup} q{qos} r{retain} m{pid}) {clientid} level({packet2.get_version()})")
        return False

    async def resume(self) -> bool:
        logging.debug(f'Beging resume for clientid: {self.waiter.connect.clientid}')
        for pid, packet in self.outgoing_inflight.items():
            now = time.time()
            if packet.get_type()==PacketType.PUBLISH:
                if  now > packet.expire_at:
                    logging.info(f'Resume {packet.pktype.name()} expired topic {packet.topic} (q{packet.get_qos()} r{int(packet.get_retain())}) to {self.waiter.connect.clientid}')
                    return False
                packet.set_expired_interval(int(packet.expire_at - now))
            packet.set_dup(True)
            data = packet.full_pack()
            await self.waiter.transport.write(data)
            logging.info(f"Resume {packet.pktype.name} (m{pid}) to {self.waiter.connect.clientid} level({packet.get_version()})")
