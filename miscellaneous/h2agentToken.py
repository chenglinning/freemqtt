import uuid
from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken

#appid = 'h2agent'
#appname = 'mqtt'
appid = 'demo2'
appname = 'mqtt'

if __name__ == "__main__":
    app = f'{appid}@{appname}'
    token = signToken(app)
    data = verifyToken(token)
    print ("******************************")
    print (token)
    print (data)
    print ("===============================")

# h2agent@mqtt
# 4JMqrmL6b63n5lPcdaLEHCBr8ZqXbtV/chU2L65pHVI=
    
#demo2@mqtt
#uOIKjO9xt8O8oc/ixUFeqFwqG2Qkdj7MUfLN9UnpjJQ=
