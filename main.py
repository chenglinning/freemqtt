# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import os
import sys
import logging
import ssl
import asyncio
import signal

import tornado.options
import tornado.autoreload
import tornado.web
from tornado.web import RequestHandler
from freemqtt.server.server import MQTTServer
from freemqtt.server.wsserver import MqttWebsocketHandler
class My404Handler(RequestHandler):
    # Override prepare() instead of get() to cover all possible HTTP methods.
    def prepare(self):
        self.set_status(404)
        self.write_error(404)

def make_app():
    return tornado.web.Application(
        [(r"/mqtt", MqttWebsocketHandler)],
    	debug=True,
        default_handler_class=My404Handler,
        websocket_ping_interval=10,
        websocket_ping_timeout=15,
    )

tornado.options.define("port", default=7883, help="Run FreeMQTT Server on a specific port", type=int)  
tornado.options.define("ssl_port", default=8883, help="Run FreeMQTT Server on a specific SSL port", type=int)  
tornado.options.define("ws_port", default=8083, help="Run FreeMQTT Server over websocket on a specific port", type=int)  
tornado.options.define("propagate", default=False, help="disable propagate", type=bool)
tornado.options.define("mqtt_via_ssl", default=False, help="enable ssl", type=bool )  

tcp_server = None
ws_server = None

def sig_handler(signum, frame):
    logging.info(f'Signal handler called with signal: {signum}')
    if tcp_server:
        tcp_server.stop()
    if ws_server:
        ws_server.stop()
    sys.exit(1)

signal.signal(signal.SIGINT, sig_handler)
#signal.signal(signal.SIGTERM, shandler)

async def main():
    tornado.options.parse_command_line()
    tornado.autoreload.start()
#   logging.basicConfig(level=logging.ERROR)
    logging.getLogger().setLevel(level=logging.DEBUG)
#   logging.getLogger().setLevel(level=logging.INFO)
    logging.info("FreeMQTT Server 1.0 started")
        
    if tornado.options.options.mqtt_via_ssl:
        certfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.crt")
        keyfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.key")
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile, keyfile)
        server = MQTTServer(ssl_options=ssl_ctx)
        mqtt_port = tornado.options.options.ssl_port
    else:
        tcp_server = MQTTServer( ssl_options=None )
        mqtt_port = tornado.options.options.port
    tcp_server.listen(mqtt_port, address="127.0.0.1")

    """
    MQTT over Websocket Server
    """
    app = make_app()
    ws_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    ws_server.listen(tornado.options.options.ws_port, address="127.0.0.1")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())