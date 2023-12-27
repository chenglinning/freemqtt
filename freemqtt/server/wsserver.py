# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import logging
from typing import Awaitable, Optional
from tornado.websocket import WebSocketHandler
from tornado.queues import Queue
from tornado.ioloop import IOLoop
from ..transport.websocket import WebsocketTranport
from .waiter import Waiter

class MqttWebsocketHandler(WebSocketHandler):

    async def open(self) -> Optional[Awaitable[None]]:
        logging.info("WebSocket opened")
        logging.info("headers: {}".format(self.request.headers))
        self.remote_ip = self.request.remote_ip
        logging.info(f"req_uri: {self.request.uri} remote_ip: {self.remote_ip}")
        self.queue = Queue()
        transport = WebsocketTranport(self)
        waiter = Waiter(transport, self.remote_ip)
        IOLoop.current().spawn_callback(waiter.start_serving)

    async def on_message(self, message) -> Optional[Awaitable[None]]:
        self.queue.put((True, message))
#       logging.info(f'Received message: {len(message)} {message}')

    def on_close(self) -> None:
        logging.info("WebSocket closed")
        self.queue.put((False, b'websocket closed'))
        self.queue.join()

    def check_origin(self, origin) -> bool:
        return True

    def select_subprotocol(self, subprotocols) -> Optional[str]:
        subprotocol = None
        logging.info(f'subprotocols: {format(subprotocols)}')
        if subprotocols and len(subprotocols) == 1:
                subprotocol = subprotocols[0]
        return subprotocol

    async def on_pong(self, data):
#       logging.info(f'R pong  {self.remote_ip}')
        pass
