# Copyright (C) ben-ning@163.com
# All rights reserved
#
import sys
import asyncio
import tornado
import signal

from freemqtt.daemonweb.command import CommandHandler
from freemqtt.server.config import MonitorCfg
freemqttp = None

def sig_handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'freemqtt monitor received signal {signame}({signum})')
    if freemqttp:
        freemqttp.terminate()
        freemqttp.wait()
        print(f"freemqtt broker stoped")
    sys.exit(1)

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

def make_app():
    return tornado.web.Application([
        (r"/cmd", CommandHandler),
    ])

async def main():
    app = make_app()
    app.listen(port = MonitorCfg.port, address = MonitorCfg.address)
#   global freemqttp
#   freemqttp = start_freemqtt_broker()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
