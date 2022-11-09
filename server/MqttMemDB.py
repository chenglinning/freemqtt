# -*- coding: utf-8 -*-
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
#
import logging
import time
import plyvel
import pickle

from tornado.ioloop import IOLoop
from .MqttCommon import Statistic_info
from .MqttSession import MqttSession
from .MqttPush2Clients import pub4pub
from ..core.MqttPublish import MqttPublish

SUB_PREFIX = b"SUB/"
PUB_PREFIX = b"PUB/"
SSS_PREFIX = b"SSE/"
STATISTIC_INFO  = b"STATISTIC_INFO"

class MqttMemDB(object):
    def __init__(self):
        self.session_dict = {} # { client_id: MqttSession }
        self.statistic = Statistic_info()
        self.persistence_db = plyvel.DB('./mqtt/data/mqttdb/', create_if_missing=True)
        self.db_restore()

    @staticmethod
    def instance():
        """
        Returns a global `MqttMemDB` instance.
        """
        if not hasattr(MqttMemDB, "_instance"):
            MqttMemDB._instance = MqttMemDB()
        return MqttMemDB._instance

    def get_pub_db(self):
        return self.persistence_db.prefixed_db(PUB_PREFIX)

    def get_client_sub_dict_from_db(self, topic):
        sub_db = self.persistence_db.prefixed_db(SUB_PREFIX)
        key = topic.encode('utf8')
        value = sub_db.get(key)
        if value:
            client_sub_dict = pickle.loads(value)
        else:
            client_sub_dict = {}
        return client_sub_dict

    def db_save_session(self, client_id):
        if client_id in self.session_dict:
            session = self.session_dict[client_id]
            sss_db = self.persistence_db.prefixed_db(SSS_PREFIX)
            value = session.getDataPickle()
            key = client_id.encode('utf8')
            sss_db.put(key, value)

    def db_delete_session(self, client_id):
        if client_id in self.session_dict:
            sss_db = self.persistence_db.prefixed_db(SSS_PREFIX)
            key = client_id.encode('utf8')
            sss_db.delete(key)
            del self.session_dict[client_id]

    def db_save_statistic(self):
        value = pickle.dumps(self.statistic)
        staistic_db = self.persistence_db.put(STATISTIC_INFO, value)
        
    def db_restore(self):
        value = self.persistence_db.get(STATISTIC_INFO)
        if value:
            self.statistic = pickle.loads(value)
        sss_db = self.persistence_db.prefixed_db(SSS_PREFIX)

        for key, value in sss_db:
            client_id = key.decode('utf8')
            session = MqttSession(self)
            session.session_data = pickle.loads(value)
            self.session_dict[client_id] = session

    def add_pub(self, mqtt_pub):
        topic = mqtt_pub.getTopic()
        key = topic.encode('utf8')
        qos = mqtt_pub.getQos()
        payload = mqtt_pub.getPayload()
        pub_db = self.persistence_db.prefixed_db(PUB_PREFIX)
        if not pub_db.get(key):
            self.statistic.inc_retain_pub()
        pub_db.put(key, pickle.dumps((qos, payload)))

    def unpub(self, mqtt_pub):
        pub_db = self.persistence_db.prefixed_db(PUB_PREFIX)
        topic = mqtt_pub.getTopic()
        key = topic.encode('utf8')
        pub_db.delete(key)

    def add_sub(self, client_id, mqtt_sub):
        session = self.session_dict[client_id]
        sub_db = self.persistence_db.prefixed_db(SUB_PREFIX)
        for (topic, qos) in mqtt_sub.sub_list:
            self.statistic.inc_sub_count()
            if qos != 0x80: # for verify ok 
                key = topic.encode('utf8')
                value = sub_db.get(key)
                if value:
                    sub_dict = pickle.loads(value)
                else:
                    sub_dict = {}
                sub_dict[client_id] = qos
                sub_db.put(key, pickle.dumps(sub_dict))
                session.add_sub(topic, qos)
            else:
                logging.info("rejected sub topic: {} from {}".format (topic, client_id))

        self.db_save_session(client_id)

    def unsub(self, client_id, mqtt_unsub):
        session = self.session_dict[client_id]
        sub_db = self.persistence_db.prefixed_db(SUB_PREFIX)
        for topic in mqtt_unsub.unsub_list:
            key = topic.encode('utf8')
            value = sub_db.get(key)
            if value:
                sub_dict = pickle.loads(value)
                if client_id in sub_dict:
                    self.statistic.dec_sub_count()
                    sub_dict.pop(client_id)
                    session.remove_sub(topic)
                    sub_db.put(key, pickle.dumps(sub_dict))
        self.db_save_session(client_id)

    def clear_sub(self, client_id):
        sub_db = self.persistence_db.prefixed_db(SUB_PREFIX)
        session = self.session_dict[client_id]
        session_sub_dict = session.get_sub_dict()
        for topic in session_sub_dict:
            key = topic.encode('utf8')
            value = sub_db.get(key)
            if value:
                sub_dict = pickle.loads(value)
                sub_dict.pop(client_id)
                sub_db.put(key, pickle.dumps(sub_dict))
                self.statistic.dec_sub_count()
        session.clear_sub()
        self.db_save_session(client_id)

    def add_session(self, context):
        if not context: return
        client_id = context.mqtt_connect.getClientId()
        clean = context.mqtt_connect.isCleanSession()
        need_resend = False
        if clean:
            if client_id in self.session_dict:
                session = self.session_dict[client_id]
                if not session.isActived():
                    self.statistic.inc_active_client()
                    session.setActived(True)
                    session.setSessionClean(clean)
                session.clear()
                session.context = context
            else:
                self.statistic.inc_total_client()
                self.statistic.inc_active_client()
                session = MqttSession(self, context=context)
                self.session_dict[client_id] = session
        else:
            if client_id in self.session_dict:
                session = self.session_dict[client_id]
                need_resend = True
                logging.info("need resend < client_id: %s >" % (client_id))
                session.context = context
                if not session.isActived():
                    session.setActived(True)
                    self.statistic.inc_active_client()
                session.setSessionClean(clean)
            else:
                session = MqttSession(self, context=context)
                self.session_dict[client_id] = session
                self.statistic.inc_total_client()
                self.statistic.inc_active_client()
        context.mqtt_session = session
        if need_resend:
            session.resend_outgoing_inflight()
        self.db_save_session(client_id)
        
    def remove_session(self, context):
        if not context: return
        client_id = context.mqtt_connect.getClientId()
        if client_id in self.session_dict:
            session = self.session_dict[client_id]
            if session.isActived():
                self.statistic.dec_active_client()
            self.statistic.dec_total_client()
            session.clear()
            self.db_delete_session(client_id)

    def session_present(self, client_id):
        return client_id in self.session_dict

    def setSessionActived(self, client_id, actived=True):
        if client_id in self.session_dict:
            session = self.session_dict[client_id]
            session.setActived(actived)
            if not actived:
                self.statistic.dec_active_client()
            logging.info("Set actived: %s  client_id: %s" % (actived, client_id))
        self.db_save_session(client_id)
                
    def get_session(self, client_id):
        return self.session_dict[client_id]

    def inc_sent_pub(self):
        self.statistic.inc_sent_pub()


    async def pub_sysinfo(self, topic, qos, payload):
        pid = 0
        payload = payload.encode('utf8')
        mqtt_pub = MqttPublish(pid, False, qos, topic, payload, False)
        await pub4pub(mqtt_pub, self)

    async def update_sys_info_topic(self):
        qos = 0
        self._timestamp = time.time()
        await self.pub_sysinfo( "$SYS/stat/clients/active", qos, str(self.statistic._active_clients) )
        await self.pub_sysinfo( "$SYS/stat/clients/total", qos, str(self.statistic._total_clients) )
        await self.pub_sysinfo( "$SYS/stat/message/received", qos, str(self.statistic._received_messages) )
        await self.pub_sysinfo( "$SYS/stat/message/sent", qos, str(self.statistic._sent_messages) )
        
        await self.pub_sysinfo( "$SYS/stat/message/retain", qos, str(self.statistic._retain_messages) )
        await self.pub_sysinfo( "$SYS/stat/subscribes/count", qos, str(self.statistic._sub_count) )
        await self.pub_sysinfo( "$SYS/stat/message/in_flight_in", qos, str(self.statistic._in_flight_i) )
        await self.pub_sysinfo( "$SYS/stat/message/in_flight_out", qos, str(self.statistic._in_flight_o) )
        await self.pub_sysinfo( "$SYS/stat/timestamp", qos, str(int(self.statistic._timestamp)) )
        self.db_save_statistic()
