# -*- coding: utf-8 -*-
# Chenglin Ning, chenglinning@gmail.com
# All rights reserved

import os
import time
import re
import logging
import struct

from io import BytesIO
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer    
from tornado.iostream import StreamClosedError
from .MqttMemDB import MqttMemDB
from .MqttContext import MqttContext

PUB_SYS_INFO_INTERVAL = 15

class MqttBroker(TCPServer):
    def __init__(self, *args, **kwargs):
        super(MqttBroker, self).__init__(*args, **kwargs)
        self.mem_db = MqttMemDB.instance()
        """
        IOLoop.current().spawn_callback(self.publish_system_info)
        """
    async def handle_stream(self, stream, address):
        context = MqttContext(stream, address)
        await context.start_loop()

    async def publish_system_info(self):
    	while True:
            await gen.sleep(PUB_SYS_INFO_INTERVAL)
            await self.mem_db.update_sys_info_topic()

