# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import toml
from collections import namedtuple

def load_toml_config(path: str) -> tuple:
    with open(path, 'r', encoding='utf-8') as f:
        toml_cfg = toml.load(f)

    TCP = namedtuple("TCP", toml_cfg["freemqtt"]["tcp"].keys()) if "tcp" in toml_cfg["freemqtt"] else None
    SSL = namedtuple("SSL", toml_cfg["freemqtt"]["ssl"].keys())  if "ssl" in toml_cfg["freemqtt"] else None
    WS = namedtuple("WS", toml_cfg["freemqtt"]["ws"].keys())  if "ws" in toml_cfg["freemqtt"] else None
    WSS = namedtuple("WSS", toml_cfg["freemqtt"]["wss"].keys()) if "wss" in toml_cfg["freemqtt"] else None
    LOG = namedtuple("WSS", toml_cfg["freemqtt"]["log"].keys()) if "log" in toml_cfg["freemqtt"] else None
    PROPS = namedtuple("PROPS", toml_cfg["freemqtt"]["properties"].keys()) if "properties" in toml_cfg["freemqtt"] else None
    MONITOR = namedtuple("MONITOR", toml_cfg["freemqtt"]["monitor"].keys()) if "monitor" in toml_cfg["freemqtt"] else None
#   DB = namedtuple("DB", toml_cfg["freemqtt"]["db"].keys())  if "db" in toml_cfg["freemqtt"] else None
    COMMON = namedtuple("COMMON", toml_cfg["freemqtt"]["common"].keys())  if "common" in toml_cfg["freemqtt"] else None

    temp_config = {
        "tcp": TCP(**toml_cfg["freemqtt"]["tcp"]) if TCP else None,
        "ssl": SSL(**toml_cfg["freemqtt"]["ssl"]) if SSL else None,
        "ws":  WS(**toml_cfg["freemqtt"]["ws"]) if WS else None,
        "wss": WSS(**toml_cfg["freemqtt"]["wss"]) if WSS else None,
        "log": LOG(**toml_cfg["freemqtt"]["log"]) if LOG else None,
        "props": PROPS(**toml_cfg["freemqtt"]["properties"]) if PROPS else None,
        "monitor": MONITOR(**toml_cfg["freemqtt"]["monitor"]) if MONITOR else None,
#       "db":  DB(**toml_cfg["freemqtt"]["db"]) if DB else None,
        "common":  COMMON(**toml_cfg["freemqtt"]["common"]) if COMMON else None,
    }
    FreeMQTT_Config = namedtuple("FreeMQTT_Config", temp_config.keys())
    freemqtt_config = FreeMQTT_Config(**temp_config)
    return freemqtt_config

tmp_cfg = load_toml_config("./config.toml")
Config = tmp_cfg.props
LogCfg = tmp_cfg.log
MonitorCfg = tmp_cfg.monitor
CommonCfg = tmp_cfg.common
