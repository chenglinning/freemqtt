import uuid
from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken
appid = 'bridge'
appname = 'mqtt'
if __name__ == "__main__":
    app = f'{appid}@{appname}'
    token = signToken(app)
    data = verifyToken(token)
    print ("******************************")
    print (token)
    print (data)
    print ("===============================")

# bridge@mqtt    
# tCWqBflYm7Rovt9W+J+oGnATU921Fh1fzoG1qxK/j0M=
