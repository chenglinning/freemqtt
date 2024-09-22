## FreeMQTTT

MQTT broker implemented in python based on asyncio (async/await)

### Features

+ Implements the full set of MQTT 3.1.1 & MQTT 5.0 (except AUTH)
+ Support QoS 0, QoS 1 and QoS 2 messages flow
+ TCP and websocket support
+ SSL support over TCP and websocket
+ Unique application isolation security mechanism
+ Sytem metrics topic: $SYS/METRICS
+ Client online notify topic:  $SYS/ONLINE
+ Client offline notify topic: $SYS/OFFLINE
+ Configuration using the TOML file

### Running environment

Python 3.9+

### Getting started

1. Get source code

```bash
$ git clone git@github.com:ningchenglin/freemqtt.git
```

2. Install dependency packages

```bash
$ cd ./freemqtt
$ python -m pip install -r requirements.txt
```

3. Run the server in foreground

```bash
$ python ./freemqttd.py
[I 240921 16:54:11 freemqttd:91] freemqttd started

```

4. Run the server in background

```bash
$ python ./freemqttctl.py start
starting freemqttd ...
start freemqttd success. 

```

5. Generate MQTT client login password (Token)

```bash
$ python ./freemqtt_token.py myapp

AppID: myapp
Token: gVRVsBqw3bQSD4CQ4rFOXtfGQMelHJmEaNlYtH7GS/A=
```

Documentation is available on [Read the Docs](https://freemqtt.cn/pages/intro.html).