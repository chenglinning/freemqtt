# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
from typing import Awaitable
from tornado.concurrent import Future
from tornado.iostream import BaseIOStream, StreamClosedError
from .exception import TransportClosedError

class TCPTranport():
    def __init__(self, stream:BaseIOStream) -> None:
        self.stream = stream

    async def read_bytes(self, n: int) -> Awaitable[bytes]:
        try:
            buff = await self.stream.read_bytes(n)
        except StreamClosedError:
            raise TransportClosedError()
        return buff

    async def write(self, data) -> Awaitable[None]:
        try:
            await self.stream.write(data)
        except StreamClosedError:
            raise TransportClosedError()

    def close(self) -> None:
        self.stream.close()
        