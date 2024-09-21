# Chenglin Ning, chenglinning@gmail.com
# All rights reserved
from tornado import gen
from tornado.tcpserver import TCPServer    
from .waiter import Waiter
from .memdb import MemDB
from ..transport import TCPTranport
PUB_SYS_INFO_INTERVAL = 15
class MQTTServer(TCPServer):
    def __init__(self, *args, **kwargs):
        super(MQTTServer, self).__init__(*args, **kwargs)
        self.mem_db = MemDB.instance()
        
    async def handle_stream(self, stream, address):
        waiter = Waiter(TCPTranport(stream), address)
        await waiter.start_serving()
