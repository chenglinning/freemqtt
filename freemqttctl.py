# Copyright (C) ben-ning@163.com
# All rights reserved
#
import sys
import os
import time
import argparse
import requests
import json
import socket

import subprocess
from freemqtt.server.config import MonitorCfg

jwtoken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhcGlrZXkiOiI5NzY2Y2MxMzFmZTg3YmM4YmNlMDRiMjZkMjIyOWYzNCJ9.u-yGcF8BF7SEi3AnNyFwdxLGy53VF1RRK2kpJDKTryI'
url = f"http://{MonitorCfg.address}:{MonitorCfg.port}/cmd"

if __name__ == "__main__":
#   print( subprocess._USE_POSIX_SPAWN, subprocess._USE_VFORK)
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="start | stop | status | restart", choices=["start", "stop", "status", "restart"])
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((MonitorCfg.address, MonitorCfg.port))
    
    si = None
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    
    if result == 0:
        sock.close()
    else:
        print ("starting freemqttd ...")
        if "freemqttctl.py" in sys.argv[0]:
            command = ["python", "./freemqttm.py"]
            p = subprocess.Popen(command, close_fds=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        else:
            command = ["./freemqttm"]
            p = subprocess.Popen(command, close_fds=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
#           p = subprocess.Popen("./freemqttm", close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        time.sleep(5)
    session = requests.Session()
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = f"Bearer {jwtoken}"

    response = session.post(url, headers=headers, data=json.dumps({"cmd": args.command}), timeout=8, proxies=None, verify=False)
    if response.status_code == 200:
        result = response.json()
    print (result["error_string"], "\n")
