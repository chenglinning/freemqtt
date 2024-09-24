## FreeMQTTT

MQTT broker implemented in python based on asyncio (async/await)

### Features

+ Implements the full set of MQTT 3.1.1 & MQTT 5.0 (except AUTH)
+ QoS0, QoS1, QoS2 support
+ MQTT over Websocket support
+ TLS/SSL support
+ Unique Application isolation security mechanism
+ Sytem metrics topic: $SYS/METRICS
+ Client online notification topic:  $SYS/ONLINE
+ Client offline notification topic: $SYS/OFFLINE
+ Configuration using the TOML file

### Running environment

Python 3.9+

### Getting started

+ Get source code

```bash
$ git clone https://github.com/chenglinning/freemqtt.git
```
+ Install dependency packages

```bash
$ cd ./freemqtt
$ python -m pip install -r requirements.txt
```

+ Run the server in foreground

```bash
$ python ./freemqttd.py
[I 240921 16:54:11 freemqttd:91] freemqttd started

```

+ Run the server in background

```bash
$ python ./freemqttctl.py start
starting freemqttd ...
start freemqttd success. 

```

+ Generate MQTT client login password (Token)

```bash
$ python ./freemqtt_token.py myapp

AppID: myapp
Token: gVRVsBqw3bQSD4CQ4rFOXtfGQMelHJmEaNlYtH7GS/A=
```

Documentation is available on [Read the Docs](https://freemqtt.cn/pages/intro.html).