# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import os
import logging
import ssl
import asyncio

import tornado.options
import tornado.autoreload
from .server import MQTTServer

tornado.options.define("port", default=7883, help="Run FreeMQTT Server on a specific port", type=int)  
tornado.options.define("ssl_port", default=8883, help="Run FreeMQTT Server on a specific SSL port", type=int)  
tornado.options.define("port_websocket", default=1885, help="Run FreeMQTT Server on a specific port", type=int)  
tornado.options.define("propagate", default=False, help="disable propagate", type=bool)
tornado.options.define("mqtt_via_ssl", default=False, help="enable ssl", type=bool )  

async def main():
    tornado.options.parse_command_line()
    tornado.autoreload.start()
    logging.info("FreeMQTT Server 1.0 started")
        
    if tornado.options.options.mqtt_via_ssl:
        certfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.crt")
        keyfile = os.path.join(os.path.abspath("."), "ssl/iot.saykey.com.key")
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile, keyfile)
        server = MQTTServer(ssl_options=ssl_ctx)
        mqtt_port = tornado.options.options.ssl_port
    else:
        server = MQTTServer( ssl_options=None )
        mqtt_port = tornado.options.options.port

    server.listen(mqtt_port, address="127.0.0.1")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())