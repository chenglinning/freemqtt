# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
#
# All rights reserved
#
#
import os
import logging
import ssl
import signal

from tornado.tcpserver import TCPServer    
from tornado.ioloop  import IOLoop    
import tornado.options
import tornado.autoreload
from .MqttBroker import MqttBroker

#tornado.options.define("port", default=1883, help="Run MQTT Broker on a specific port", type=int)  
tornado.options.define("port", default=7883, help="Run MQTT Broker on a specific port", type=int)  
tornado.options.define("ssl_port", default=8883, help="Run MQTT Broker on a specific SSL port", type=int)  
tornado.options.define("port_websocket", default=1885, help="Run MQTT Server on a specific port", type=int)  
tornado.options.define("propagate", default=False, help="disable propagate", type=bool)
tornado.options.define("mqtt_via_ssl", default=False, help="enable ssl", type=bool )  

def mqtt_server_main():
    tornado.options.parse_command_line()
    tornado.autoreload.start()
    logging.info("Magpie MQTT Broker 3.0 started")
        
    if tornado.options.options.mqtt_via_ssl:
        certfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.crt")
        keyfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.key")
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile, keyfile)
        server = MqttBroker(ssl_options=ssl_ctx)
        mqtt_port = tornado.options.options.ssl_port
    else:
        server = MqttBroker( ssl_options=None )
        mqtt_port = tornado.options.options.port
    server.listen(mqtt_port, address="127.0.0.1")
#   server.listen(mqtt_port)

    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        print ("ctrol+c exited")
    finally:
        IOLoop.current().stop()       # might be redundant, the loop has already stopped
        IOLoop.current().close(True)  # need
        print ("ctrol+c exited-------------")

if __name__ == '__main__':

    """
    signal.signal(signal.SIGSTP, _signal_hander)
    signal.signal(signal.SIGKILL, _signal_hander)
    signal.signal(signal.SIGTERM, _signal_hander)
    signal.signal(signal.SIGINT, _signal_hander)
    """

    mqtt_server_main()
