# -*- coding: utf-8 -*-
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#

import logging
from tornado.ioloop import IOLoop    
from .MqttCommon import SessionData
from .MqttPush2Clients import stream_write
from ..core.MqttException import MqttException

class MqttSession(object):
    def __init__(self, mem_db, context=None):
        super(MqttSession, self).__init__()
        self.mem_db = mem_db
        self.context = context
        self.session_data = SessionData(context.mqtt_connect) if context else None
        self.active = True if context else False
        
    def clear(self):
        self.mem_db.clear_sub(self.getClientId())
        self.session_data.clear()

    def resend_outgoing_inflight(self):
        logging.info("RESENT outgoing inflight 000000000000 < client_id: %s >" % (self.getClientId()))
        msg_dict = self.session_data.get_outgoing_inflight_messages()

        for pid in msg_dict:
            mqtt_message = self.session_data.get_outgoing_inflight_message(pid)
            mqtt_message.setDup(True)
            msgtype = mqtt_message.getType()
            data = mqtt_message.pack()
            IOLoop.current().spawn_callback(stream_write, self, data)
            logging.info("RESENT outgoing inflight < type: %d  pid: %d  client_id: %s >" % (msgtype, pid, self.getClientId()))

    def getClientId(self):
        return self.session_data.getClientId()

    def getNextPid(self):
        return self.session_data.getNextPid()
            
    def verifyIncomingInflightMessage(self, pid, msgtype):
        return self.session_data.verifyIncomingInflightMessage(pid, msgtype)

    def verifyOutgoingInflightMessage(self, pid, msgtype):
        return self.session_data.verifyOutgoingInflightMessage(pid, msgtype)
    
    def add_incoming_inflight_message(self, mqtt_message):
        self.session_data.add_incoming_inflight_message(mqtt_message)
            
    def add_outgoing_inflight_message(self, mqtt_message):
        self.session_data.add_outgoing_inflight_message(mqtt_message)
            
    def remove_incoming_inflight_message(self, pid):
        self.session_data.remove_incoming_inflight_message(pid)
            
    def remove_outgoing_inflight_message(self, pid):
        self.session_data.remove_outgoing_inflight_message(pid)

    def isAlreadIncomingInflightMessage(self, pid):
        return self.session_data.isAlreadIncomingInflightMessage(pid)

    def isAlreadOutgoingInflightMessage(self, pid):
        return self.session_data.isAlreadOutgoingInflightMessage(pid)

    def add_sub(self, topic, qos):
        self.session_data.add_sub(topic, qos)

    def remove_sub(self, topic):
        self.session_data.remove_sub(topic)

    def getDataPickle(self):
        return self.session_data.getPickle()

    def get_sub_dict(self):
        return self.session_data.get_sub_dict()

    def clear_sub(self):
        self.session_data.clear_sub()

    def isActived(self):
        return self.active

    def setActived(self, actived):
        self.active = actived

    def setSessionClean(self, clean):
        self.session_data.setSessionClean(clean)

    def isSessionClean(self):
        return self.session_data.isSessionClean()

    def isPresentRetainedTopic(self, topic):
        return self.session_data.isPresentRetainedTopic(topic)

    def getRetainedTopicCount(self):
        return self.session_data.getRetainedTopicCount()

    def add_retain_pub(self, topic):
        self.session_data.add_retain_pub(topic)
