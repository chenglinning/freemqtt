# -*- coding: utf-8 -*-
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#
import time
import pickle
from ..core.MqttException import MqttException

class Statistic_info:
    def __init__(self):
        self._active_clients = 0
        self._total_clients = 0
        self._received_messages = 0
        self._sent_messages = 0
        self._sub_count = 0
        self._retain_messages = 0
        self._in_flight_o = 0
        self._in_flight_i = 0
        self._timestamp = time.time()

    def inc_active_client(self):
        self._active_clients += 1
    def dec_active_client(self):
        self._active_clients -= 1

    def inc_total_client(self):
        self._total_clients += 1
    def dec_total_client(self):
        self._total_clients -= 1

    def inc_recv_pub(self):
        self._received_messages += 1

    def inc_sent_pub(self):
        self._sent_messages += 1

    def inc_retain_pub(self):
        self._retain_messages += 1

    def dec_retain_pub(self):
        self._retain_messages -= 1

    def inc_sub_count(self):
        self._sub_count += 1

    def dec_sub_count(self):
        self._sub_count += 1

    def inc_in_flight_i(self):
        self._in_flight_i += 1

    def dec_in_flight_i(self):
        self._in_flight_i -= 1

    def inc_in_flight_o(self):
        self._in_flight_o += 1

    def dec_in_flight_o(self):
        self._in_flight_o -= 1

    def getPickle(self):
        return pickle.dumps(self)


class SessionData(object):
    def __init__(self, mqtt_connect):
        self.sub_dict = {} # { subtopic: qos }
        self.retained_pub_dict = {} # { topic: timestamp }
        
        '''
            { mid: MqttMessage} for incoming message in-flight
        '''
        self.incoming_inflight = {}
        
        '''
            { mid: MqttMessage} for outgoing message in-flight
            Now just allow this dictionary has one element, i.e. only one publish message within outgoing in-flight window  
        '''

        self.outgoing_inflight = {}
        self.curr_pid = 0

        self.clean_session = mqtt_connect.isCleanSession()
        self.client_id = mqtt_connect.getClientId()
        self.user_name = mqtt_connect.getUserName()
        self.user_password = mqtt_connect.getUserPassword()
        
        """        
        self.keep_alive_interval = mqtt_connect.getKeepAliveInterval() 
        self.will = mqtt_connect.hasWill()
        self.will_qos = mqtt_connect.will_qos
        self.will_retain = mqtt_connect.will_retain
        self.will_topic = mqtt_connect.will_topic
        self.will_message = mqtt_connect.will_message
        """

    def clear(self):
        self.sub_dict.clear()
        self.curr_pid = 0
        self.outgoing_inflight.clear()
        self.incoming_inflight.clear()
        self.retained_pub_dict.clear()

    def getNextPid(self):
        count = 0
        while True:
            self.curr_pid = (self.curr_pid + 1) % 65536
            if self.curr_pid and self.curr_pid not in self.outgoing_inflight:
                return self.curr_pid
            count += 1
            if count == 65536:
                raise MqttException(0, MqttException.REASON_CODE_NO_AVAILABLE_PACKET_ID)

    def getClientId(self):
        return self.client_id

    def getPickle(self):
        return pickle.dumps(self)

    def verifyIncomingInflightMessage(self, pid, msgtype):
        result = False
        if pid in self.incoming_inflight:
            if self.incoming_inflight[pid].getType() == msgtype:
                result = True
        return result

    def verifyOutgoingInflightMessage(self, pid, msgtype):
        result = False
        if pid in self.outgoing_inflight:
            if self.outgoing_inflight[pid].getType() == msgtype:
                result = True
        return result
    
    def add_incoming_inflight_message(self, mqtt_message):
        pid = mqtt_message.getPid()
        self.incoming_inflight[pid] = mqtt_message
            
    def add_outgoing_inflight_message(self, mqtt_message):
        pid = mqtt_message.getPid()
        self.outgoing_inflight[pid] = mqtt_message
            
    def remove_incoming_inflight_message(self, pid):
        self.incoming_inflight.pop(pid, None)
            
    def remove_outgoing_inflight_message(self, pid):
        self.outgoing_inflight.pop(pid, None)

    def isAlreadIncomingInflightMessage(self, pid):
        result = False
        if pid in self.incoming_inflight:
            result = True
        return result

    def isAlreadOutgoingInflightMessage(self, pid):
        result = False
        if pid in self.outgoing_inflight:
            result = True
        return result

    def add_sub(self, topic, qos):
        self.sub_dict[topic] = qos

    def remove_sub(self, topic):
        self.sub_dict.pop(topic, None)

    def get_sub_dict(self):
        return self.sub_dict

    def clear_sub(self):
        self.sub_dict.clear()
        
    def setSessionClean(self, clean):
        self.clean_session = clean

    def isSessionClean(self):
        return self.clean_session

    def get_outgoing_inflight_messages(self):
        return self.outgoing_inflight

    def get_outgoing_inflight_message(self, pid):
        return self.outgoing_inflight[pid]

    def isPresentRetainedTopic(self, topic):
        return topic in self.retained_pub_dict

    def getRetainedTopicCount(self):
        return len(self.retained_pub_dict)

    def add_retain_pub(self, topic):
        self.retained_pub_dict[topic] = int(time.time())

    def clear_expiried_retain_pub(self):
        pass
