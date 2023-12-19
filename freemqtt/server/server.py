# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
from tornado import gen
from tornado.tcpserver import TCPServer    
from .waiter import Waiter
from .memdb import MemDB

PUB_SYS_INFO_INTERVAL = 15
class MQTTServer(TCPServer):
    def __init__(self, *args, **kwargs):
        super(MQTTServer, self).__init__(*args, **kwargs)
        self.mem_db = MemDB.instance()
        """
        IOLoop.current().spawn_callback(self.publish_system_info)
        """
    async def handle_stream(self, stream, address):
        waiter = Waiter(stream, address)
        await waiter.start_serving()

    async def publish_system_info(self):
    	while True:
            await gen.sleep(PUB_SYS_INFO_INTERVAL)
            await self.mem_db.update_sys_info_topic()

