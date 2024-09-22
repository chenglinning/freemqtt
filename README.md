## FreeMQTTT
A MQTT Server in Python
### Feature
::: FreeMQTT's unique application isolation security mechanism

+ FreeMQTT assigns each incoming MQTT client to a separate independent Application
+ FreeMQTT generates a token Token for each Application using the freemqtt_token command (multiple tokens can be generated)
+ The token Token contains the Application ID and is encrypted and signed with the secret key
+ MQTT clients connecting to FreeMQTT pass the token Token as the password in the connect method
+ FreeMQTT verifies the authentication by decrypting and verifying the signature when receiving the CONNECT message
+ If FreeMQTT authenticates successfully, it will obtain the Application ID of the MQTT client from the token Token
+ Different Applications are independent of each other, and Application A can have an A client, while Application B can have a B client.