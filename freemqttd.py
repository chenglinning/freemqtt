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
import argparse

import tornado.autoreload
import tornado.web
from tornado.options import define, options
from tornado.web import RequestHandler
from freemqtt.server.server import MQTTServer
from freemqtt.server.wsserver import MqttWebsocketHandler
from freemqtt.server.config import load_toml_config

#  sudo docker run -itd -p 1883:1883 -w /freemqttd --name tencent-freemqtt tencent-freemqt-img /freemqttd/freemqttd
#  sudo docker run -itd -p 1883:1883 --name freemqtt-container freemqtt-img

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

"""
tornado.options.define("port", default=7883, help="Run FreeMQTT Server on a specific port", type=int)  
tornado.options.define("ssl_port", default=8883, help="Run FreeMQTT Server on a specific SSL port", type=int)  
tornado.options.define("ws_port", default=8083, help="Run FreeMQTT Server over websocket on a specific port", type=int)  
tornado.options.define("propagate", default=False, help="disable propagate", type=bool)
tornado.options.define("mqtt_via_ssl", default=False, help="enable ssl", type=bool )  
"""

define("propagate", default=False, help="disable propagate", type=bool)
define("daemon", default=False, help="enabel daemon", type=bool)

tcp_server = None
ssl_server = None
ws_server = None
wss_server = None

def sig_handler(signum, frame):
    signame = signal.Signals(signum).name
    logging.info(f'FreeMQTT broker received signal: {signame}({signum})')
    if tcp_server:
        tcp_server.stop()
    if ws_server:
        ws_server.stop()
    if ssl_server:
        ssl_server.stop()
    if wss_server:
        wss_server.stop()
    sys.exit(1)

# KeyboardInterrupt
signal.signal(signal.SIGINT, sig_handler)
# Terminate signal
signal.signal(signal.SIGTERM, sig_handler)

# python freemqtt_broker.py --daemon --log_file_prefix=./log/freemqtt.log

async def main():
    options.parse_command_line()
    tornado.autoreload.start()

#   logging.basicConfig(level=logging.ERROR)
#   logging.getLogger().setLevel(level=logging.DEBUG)
#   logging.getLogger().setLevel(level=logging.INFO)

    mqttcfg = load_toml_config("./config.toml")
#   print("starting freemqtt broker...")

    """
    parse = argparse.ArgumentParser()
    parse.add_argument("-D", "--daemon", help="run as daemon", action="store_true")
    args = parse.parse_args()
    """

    logging.info("freemqttd started")

    """
    MQTT over tcp
    """
    if mqttcfg.tcp:
        global tcp_server
        tcp_server = MQTTServer( ssl_options=None )
        tcp_server.listen(mqttcfg.tcp.port, address=mqttcfg.tcp.address)

    """
    MQTT over ssl
    """
    if mqttcfg.ssl:
        global ssl_server
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(mqttcfg.ssl.ssl_certificate, mqttcfg.ssl.ssl_certificate_key)
        ssl_server = MQTTServer(ssl_options=ssl_ctx)
        ssl_server.listen(mqttcfg.ssl.port, address=mqttcfg.ssl.address)

    """
    MQTT over Websocket Server
    """
    app = make_app()
    if mqttcfg.ws:
        global ws_server
        ws_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        ws_server.listen(mqttcfg.ws.port, address=mqttcfg.ws.address)

    """
    MQTT over Websocket Server over ssl
    """
    if mqttcfg.wss:
        global wss_server
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(mqttcfg.wss.ssl_certificate, mqttcfg.wss.ssl_certificate_key)
        wss_server = tornado.httpserver.HTTPServer(app, xheaders=True, ssl_options=ssl_ctx)
        wss_server.listen(mqttcfg.wss.port, address=mqttcfg.wss.address)
    await asyncio.Event().wait()
    logging.info("freemqttd stoped")
    
if __name__ == "__main__":
    asyncio.run(main())
