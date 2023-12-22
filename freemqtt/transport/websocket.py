# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import logging
from typing import Awaitable
from tornado.websocket import WebSocketClosedError
from tornado.concurrent import Future

from .exception import TransportClosedError

class WebsocketTranport():
    def __init__(self, ws_stream):
        self.ws_stream = ws_stream
        self.buffer = bytes()
        
    async def read_bytes(self, n: int) -> Awaitable[bytes]:
        blen = len(self.buffer)
        while blen<n:
            valid, data = await self.ws_stream.queue.get()
            if valid:
                self.buffer += data
                blen = len(self.buffer)
                self.ws_stream.queue.task_done()
            else:
                raise TransportClosedError()
        rbuff = self.buffer[0:n]
        self.buffer = self.buffer[n:]
        return rbuff
    
    async def write(self, data) -> Awaitable[None]:
        try:
            await self.ws_stream.write_message(data, binary=True)
        except WebSocketClosedError:
            raise TransportClosedError()

    def close(self) -> None:
        self.ws_stream.close()
