import time, random, logging
from typing import Dict, Set, Tuple, List
from copy import copy
from tornado.ioloop import IOLoop

from ..mqttp.publish import Publish
from ..mqttp.subscribe import Subscribe, TopicOptPair
from ..mqttp.packet import Packet
from .waiter import Waiter as Waiter2
from .session import MQTTSession
from .common import State, SubOption, ClientID, AppID, Topic, TopicFilter, SharedTopicRegexp, ShareName
class MqttApp(object):
    def __init__(self, appid: AppID, appname: str="freemqtt") -> None:
        # mqtt application id & name
        self.appid = appid
        self.appname = appname
        self.connect_max = 128
        
        self.sei = 1800  # default session expire interval

        # Statistic data for the Application
        self.curr_conn_num = 0
        self.active_clients = 0
        self.total_clients = 0
        self.received_messages = 0
        self.sent_messages = 0
        self.sub_count = 0
        self.retain_messages = 0
        self.inflight_out = 0
        self.inflight_in = 0

        # sessions database
        self.ssdb: Dict[ClientID, MQTTSession] = {}
        
        # no share subscription database
        self.subdb: Dict[TopicFilter, Dict[ClientID, SubOption]] = {}

        # share subscription database
        self.sharedb: Dict[ShareName, Dict[TopicFilter, Dict[ClientID, SubOption]]] = {}

        # Topic filter matched topics of retain message
        self.tf_retain_topics: Dict[TopicFilter, Set[Topic]] = {}
        # retain message
        self.retain_msg: Dict[Topic, Packet] = {}

    def addSubscription(self, tf: TopicFilter, top: TopicOptPair, clientid: ClientID) -> None:
        subopt = SubOption(options=top.options, subid=top.sub_id)
        if SharedTopicRegexp.match(tf):
            top.shared = True
            # share topic filter
            tflist = tf.split('/')
            sharename = tflist[1]
            tf2 = '/'.join(tflist[2:])
            shareGroup = self.sharedb.get(sharename, dict())
            csubopts = shareGroup.get(tf2, dict())
            top.existing = clientid in csubopts
            csubopts[clientid] = subopt
            shareGroup[tf2] = csubopts
            self.sharedb[sharename] = shareGroup
        else:
            # not share topic filter
            top.shared = False
            csubopts = self.subdb.get(tf, dict())
            top.existing = clientid in csubopts
            csubopts[clientid] = subopt
            self.subdb[tf] = csubopts

    def delSubscription(self, tf: TopicFilter, clientid: ClientID) -> None:
        if SharedTopicRegexp.match(tf):
            # share topic filter
            tflist = tf.split('/')
            sharename = tflist[1]
            tf2 = '/'.join(tflist[2:])
            shareGroup = self.sharedb.get(sharename, dict())
            csubopts = shareGroup.get(tf2, dict())
            csubopts.pop(clientid, None)
            if csubopts:
                shareGroup[tf2] = csubopts
            else:
                shareGroup.pop(tf2, None)
            if shareGroup:                
                self.sharedb[sharename] = shareGroup
            else:
                self.sharedb.pop(sharename, None)
        else:
            csubopts = self.subdb.get(tf, dict())
            csubopts.pop(clientid, None)
            if csubopts:
                self.subdb[tf] = csubopts
            else:
                self.subdb.pop(tf, None)            

    def getSession(self,clientid: ClientID) -> MQTTSession:
        return self.ssdb.get(clientid)
    
    def getWaiter(self, clientid: ClientID) -> Waiter2:
        if clientid in self.ssdb:
            waiter = self.ssdb.get(clientid).waiter
        else:
            waiter = None
        return waiter
    
    def getSubscribersDict(self, tf: TopicFilter) -> Dict[ClientID, SubOption]:
        c2subs = {}
        subs = self.subdb.get(tf, {})
        for clientid, suboption in subs.items():
            session = self.getSession(clientid)
            if session:
                if session.waiter.state==State.CONNECTED or session.waiter.state==State.WAITING_EXPIRED:
                    c2subs[clientid] = suboption
        return c2subs
    
    def getSharedSubscribersDict(self, tf: TopicFilter) -> Dict[ShareName, Tuple[ClientID, SubOption]]:
        sc2subs: Dict[ShareName, Tuple[ClientID, SubOption]] = {}
        for sharename, sharegroup in self.sharedb.items():
            subs = sharegroup.get(tf, {})
            c2subs: Dict[ClientID, SubOption] = {}
            for clientid, suboption in subs.items():
                session = self.getSession(clientid)
                if session.waiter.state==State.CONNECTED:
                    c2subs[clientid] = suboption
            if len(c2subs) > 0:
                clientid = random.choice([key for key in subs])
                suboption = c2subs[clientid]
                sc2subs[sharename] = (clientid, suboption)
        return sc2subs

    def sessionPresent(self, clientid: ClientID) -> bool:
        return clientid in self.ssdb
    
    def addSession(self, clientid: ClientID, waiter: Waiter2) -> None:
        oldsession = self.ssdb.pop(clientid, None)
        if oldsession:
            for tf in oldsession.topicFilterSet:
                self.subdb[tf].pop(clientid, None)
            oldsession.topicFilterSet.clear()
            del oldsession
        self.ssdb[clientid] = MQTTSession(waiter)

    def delSession(self, clientid: ClientID) -> None:
        session = self.ssdb.pop(clientid, None)
        if session:
            for tf in session.topicFilterSet:
                self.subdb[tf].pop(clientid, None)
            session.topicFilterSet.clear()
            del session

    def enumerateTopicFilter(self, tlist: List[str], pos: int, n: int, li: List[str]) -> None:
        if pos < n:
            tl0 = copy(tlist)
            tl1 = copy(tlist)
            tl1[pos] = '+'
            li.append('/'.join(tl1))
            tlx = tl1[0:pos]
            tlx.append('#')
            li.append('/'.join(tlx))
            pos += 1
            self.enumerateTopicFilter(tl0, pos, n, li)
            self.enumerateTopicFilter(tl1, pos, n, li)
        else:
            return
        
    def getTFList(self, topic: Topic) -> List[TopicFilter]:
        li = list()
        elist = topic.split('/')
        n = len(elist)
        li.append(topic)
        pos = 0
        self.enumerateTopicFilter(elist, 0, n, li)
        return li
    
    async def dispatch(self, packet: Publish) -> None:
        topic = packet.topic
        qos = packet.get_qos()
        payload = packet.payload
        tflist = self.getTFList(topic)
        # for not shared subscriptions
        for tf in tflist:
            subs = self.getSubscribersDict(tf)
            for clientid, suboption in subs.items():
                session = self.getSession(clientid)
                if session:
                    IOLoop.current().spawn_callback(session.delivery, packet, suboption, False)

        # for shared subscriptions
        for tf in tflist:
            sc2subs = self.getSharedSubscribersDict(tf)
            for sharename, (clientid, suboption) in sc2subs.items():
                session = self.getSession(clientid)
                if session:
                    logging.info(f'$Share/{sharename}/{tf} Clientid({clientid})')
                    IOLoop.current().spawn_callback(session.delivery, packet, suboption, True)

    async def dispatchRetainMessages(self, packet:Subscribe, clientid:ClientID) -> None:
        session = self.getSession(clientid)
        if not session:
            return
        for top in packet.topicOpsList:
            if top.shared or top.RH()==2 or not top.valid:
                continue
            if top.existing and top.RH()==1:
                continue
            suboption = SubOption(options=top.options, subid=top.sub_id)
            tpset = self.tf_retain_topics.get(top.topic_filter, set())
            for topic in tpset:
                message = self.retain_msg.get(topic, None)
                if message:
                    if  time.time() < message.expire_at:
                        IOLoop.current().spawn_callback(session.delivery, message, suboption, False)
                    else:
                        self.removeRetainMsg(message)
                        logging.info(f'topic({message.topic}) q({message.get_qos()}) expired')

    def storeRetainMsg(self, packet: Publish) -> None:
        topic = packet.topic
        self.retain_msg[topic] = packet
        tflist = self.getTFList(topic)
        for tf in tflist:
            tpset = self.tf_retain_topics.get(tf, set())
            tpset.add(topic)
            self.tf_retain_topics[tf] = tpset
    
    def removeRetainMsg(self, packet: Publish) -> None:
        topic = packet.topic
        self.retain_msg.pop(topic, None)
        tflist = self.getTFList(topic)
        for tf in tflist:
            tpset = self.tf_retain_topics.get(tf, set())
            tpset.discard(topic)
            self.tf_retain_topics[tf] = tpset

class MemDB(object):
    def __init__(self):
        self.apps: Dict[AppID, MqttApp] = {}

    @staticmethod
    def instance():
        """
        Returns a global `MemDB` instance.
        """
        if not hasattr(MemDB, "_instance"):
            MemDB._instance = MemDB()
        return MemDB._instance
    
    def getApp(self, appid: AppID) -> MqttApp:
        if not appid in self.apps:
            self.apps[appid] = MqttApp(appid=appid)
        return self.apps[appid]

