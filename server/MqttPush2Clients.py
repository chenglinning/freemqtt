# -*- coding: utf-8 -*-
# Chenglin Ning, chenglinning@gmail.com
#
import re
import logging
import pickle

from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from ..core.MqttPublish import MqttPublish

SUB_PREFIX = b"SUB/"
PUB_PREFIX = b"PUB/"

async def pub2client(client_id, topic, qos, payload, mem_db):
    session = mem_db.get_session(client_id)
    pid = session.getNextPid() if qos>0 else 0
    mqtt_pub = MqttPublish(pid, False, qos, topic, payload, False)
    if qos:
        session.add_outgoing_inflight_message(mqtt_pub)
        logging.info("PUBLISH in outgoing (d%d, q%d, r%d, m%d), topic: %s, client_id: %s" % (0, qos, 0, pid, topic, client_id))

    if session.isActived():
        data = mqtt_pub.pack()
        await stream_write(session, data)
        if qos == 0:
            mem_db.inc_sent_pub()
        logging.info("PUBLISH sent (d%d, q%d, r%d, m%d), topic: %s, client_id: %s" % (0, qos, 0, pid, topic, client_id))

async def pub4pub2(topic, topic_filter, qos, payload, mem_db):
    logging.info('topic_filter: {}'.format(topic_filter))
    client_sub_dict = mem_db.get_client_sub_dict_from_db(topic_filter)
    logging.info('client_sub_dirc: {}'.format(client_sub_dict))
    for client_id, sub_qos in client_sub_dict.items():
        logging.info('client_id: {}'.format(client_id))
        pub_qos = min(sub_qos, qos)
        IOLoop.current().spawn_callback(pub2client, client_id, topic, pub_qos, payload, mem_db)

async def stream_write(session, data):
    if session.context.state==2:
        remote_ip = session.context.remote_ip
        try:
            await session.context.stream.write(data)
        except StreamClosedError:
            await session.context.closed_handler()
            logging.error("%s be closed.", remote_ip)
        finally:
            pass

async def pub4pub(mqtt_pub, mem_db):
    topic = mqtt_pub.getTopic()
    qos = mqtt_pub.getQos()
    payload = mqtt_pub.getPayload()
    topic_filter = topic
    await pub4pub2(topic, topic_filter, qos, payload, mem_db)

    """
    li =  topic.split('/')
    if len(li)>1:
        li[-1] = "+"
        topic_filter = "/".join(li)
        await pub4pub2(topic, topic_filter, qos, payload, mem_db)
    while len(li)>1:
        li[-1] = "#"
        topic_filter = "/".join(li)
        await pub4pub2(topic, topic_filter, qos, payload, mem_db)
        li.pop()
    """
    li =  topic.split('/')
    li[1] = '+'
    topic_filter = "/".join(li)
    await pub4pub2(topic, topic_filter, qos, payload, mem_db)

async def pub4sub(mqtt_sub, mem_db, client_id):
    sub_list = mqtt_sub.sub_list
    session = mem_db.get_session(client_id)
    pub_db = mem_db.get_pub_db()

    for (topic, sub_qos) in sub_list:
        if sub_qos != 0x80:
            topic_type = 0
            _topic = topic
            if topic[-1]=='+':
                topic_type = 1
                _topic = topic[:-2]
                _prefix = _topic.encode('utf8')
            elif topic[-1]=='#':
                topic_type = 2
                _topic = topic[:-2]
                _prefix = _topic.encode('utf8')

            if topic_type==0:
                key = _topic.encode('utf8')
                value = pub_db.get(key)
                if value:
                    qos, payload = pickle.loads(value)
                    pub_qos = min(sub_qos, qos)
                    session = mem_db.get_session(client_id)
                    await pub2client(client_id, topic, pub_qos, payload, mem_db)

            elif topic_type==1:
                _level = len(_topic.split('/')) + 1
                with pub_db.iterator(prefix=_prefix) as it:
                    for key, value in it:
                        _topic2 = key.encode('utf8')
                        curr_level = len(_topic2.split('/'))
                        if curr_level == _level:
                            if value:
                                qos, payload = pickle.loads(value)
                                pub_qos = min(sub_qos, qos)
                                session = mem_db.get_session(client_id)
                                await pub2client(client_id, _topic2, pub_qos, payload, mem_db)
            elif topic_type==2:
                with pub_db.iterator(prefix=_prefix) as it:
                    for key, value in it:
                        _topic2 = key.decode('utf8')
                        if value:
                            qos, payload = pickle.loads(value)
                            pub_qos = min(sub_qos, qos)
                            session = mem_db.get_session(client_id)
                            await pub2client(client_id, _topic2, pub_qos, payload, mem_db)
