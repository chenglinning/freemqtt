# Copyright (C) 2020-2028 
# Chenglin Ning, chenglinning@gmain.com
#

import time, datetime
import subprocess
from .base import BaseHandler
from enum import IntEnum
from ..server.config import load_toml_config

class State(IntEnum):
    stop = 0
    running = 1

status = State.stop
start_time = int(time.time())
stop_time = int(time.time())

freemqttd_p = None

def start_freemqtt_broker():
    global freemqttd_p, status, start_time
    LogCfg = load_toml_config("./config.toml").log
    cmdline = f"python freemqttd.py --daemon --log-file-prefix={LogCfg.path} --log-file-max-size={LogCfg.maxim_size} --logging={LogCfg.log_level}"
    p = subprocess.Popen(cmdline, close_fds=False)
    start_time = int(time.time())
    return p

# freemqtt RUNNING   pid 381527, uptime 91 days, 16:45:27
def uptime(fromtime):
    diff = int(time.time()) - fromtime
    days = diff // 86400
    hours = (diff % 86400) // 3600
    minutes = (diff % 3600) // 60
    seconds = diff % 60
    return (days, hours, minutes, seconds)

class CommandHandler(BaseHandler):
    def check_request_json_data(self):
        if not self.check_json_item('cmd', str):
            return False
        return True
    
    async def my_handler(self):
        global freemqttd_p, status, start_time, stop_time
        if freemqttd_p:
            if freemqttd_p.poll() is None:
                pass
            else:
                status = State.stop
                freemqttd_p = None

        cmd = self._request['cmd']
        if cmd=="status":
            if status==State.running:
                days, hours, minutes, seconds = uptime(start_time)
                msg = f"freemqttd RUNNING pid {freemqttd_p.pid}, uptime {days} days, {hours}:{minutes}:{seconds}"
                self.set_error_string(msg)
            elif status==State.stop: 
                dt = datetime.datetime.fromtimestamp(stop_time)
                msg = f"freemqttd STOPPED, {dt}"
                self.set_error_string(msg)
        elif cmd=="start":
            if status==State.stop:
                freemqttd_p = start_freemqtt_broker()
                self.set_error_string("start freemqttd success.")
                status = State.running
            elif status==State.running:
                self.set_error_code(6002)
            else:
                self.send_error(1)
                self.set_error_string("start freemqttd fail.")
        elif cmd=="stop":
            if status==State.running:
                freemqttd_p.terminate()
                freemqttd_p.wait()
                status = State.stop
                stop_time = int(time.time())
                self.set_error_string("stop freemqttd success.")
            else:
                self.set_error_code(6003)
        elif cmd=="restart":
            if status==State.running:
                freemqttd_p.terminate()
                freemqttd_p.wait()
                status = State.stop
                stop_time = int(time.time())
            freemqttd_p = start_freemqtt_broker()
            status = State.running
            self.set_error_string("restart freemqttd success.")
