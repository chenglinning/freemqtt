import logging
import time
from typing import Dict
from tornado.ioloop import IOLoop
from .session import MQTTSession
from ..mqttp.connect import Connect
from ..mqttp.publish import Publish
from .waiter import MQTTServer

class MemDB(object):
    def __init__(self):
        self.apps: Dict[str, MqttApp] = {}

    @staticmethod
    def instance():
        """
        Returns a global `MemDB` instance.
        """
        if not hasattr(MemDB, "_instance"):
            MemDB._instance = MemDB()
        return MemDB._instance

class MqttApp(object):
    def __init__(self, appid: int, appname: str) -> None:
        # mqtt application id & name
        self.appid = appid
        self.appname = appname
        
        # Statistic data
        self.curr_conn_num = 0
        self.active_clients = 0
        self.total_clients = 0
        self.received_messages = 0
        self.sent_messages = 0
        self.sub_count = 0
        self.retain_messages = 0
        self.inflight_out = 0
        self.inflight_in = 0

        # session & context map
        self.sessions : Dict[str, MQTTSession] = {} # {clientid: MQTTSession}
        self.context_map : Dict[str, MQTTServer] = {} # {clientid: MQTTServer}

    def get_session(self, clientid: str) -> MQTTSession:
        return self.sessions.get(clientid, None)

    def get_context(self, clientid: int) -> MQTTServer:
        return self.context_map.get(clientid, None)
