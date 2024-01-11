from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken
appid = '68ed2da2'
appname = 'demo'
if __name__ == "__main__":
    app = f'{appname}@{appid}'
    token = signToken(app)
    data = verifyToken(token)
    print ("******************************")
    print (token)
    print (data)
    print ("===============================")

# for guojie_app 
# hx5hMRJ8z+5guo7qh6RNZPsw3quEOT+n50lyGCZg09A=
        
# demo
# wNMAP5SRt53QkEf47mLrbBVDqcRtiuHlLAUMQxSPG1E=