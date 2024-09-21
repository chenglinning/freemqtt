import argparse
import uuid
from freemqtt.server.tokentools import signToken, verifyToken
# appid = uuid.uuid1().hex[0:8]
# appname = 'demo'
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("appid", help="freemqtt appid")
    args = parser.parse_args()
    app = args.appid
    token = signToken(app)
    data = verifyToken(token)
    print (f"\nAppID: {data}")
    print (f"Token: {token}")
    
# for guojie_app 
# hx5hMRJ8z+5guo7qh6RNZPsw3quEOT+n50lyGCZg09A=
# demo
# wNMAP5SRt53QkEf47mLrbBVDqcRtiuHlLAUMQxSPG1E=