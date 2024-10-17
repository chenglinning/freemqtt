import logging
import os, sys
import signal
import time
import asyncio
import gmqtt

AppID = "myapp"
Token = "F94oTEPrikcIUVWRsm1NMc1SoLxSQ9s0bUiZRP1ndIw="

STOP = asyncio.Event()


def on_connect(client, flags, rc, properties):
    logging.info('[CONNECTED {}]'.format(client._client_id))


def on_message(client, topic, payload, qos, properties):
    logging.info('[RECV MSG {}] TOPIC: {} PAYLOAD: {} QOS: {} PROPERTIES: {}'
                 .format(client._client_id, topic, payload, qos, properties))


def on_disconnect(client, packet, exc=None):
    logging.info('[DISCONNECTED {}]'.format(client._client_id))


def on_subscribe(client, mid, qos, properties):
    # in order to check if all the subscriptions were successful, we should first get all subscriptions with this
    # particular mid (from one subscription request)
    subscriptions = client.get_subscriptions_by_mid(mid)
    for subscription, granted_qos in zip(subscriptions, qos):
        # in case of bad suback code, we can resend  subscription
        if granted_qos >= gmqtt.constants.SubAckReasonCode.UNSPECIFIED_ERROR.value:
            logging.warning('[RETRYING SUB {}] mid {}, reason code: {}, properties {}'.format(
                            client._client_id, mid, granted_qos, properties))
            client.resubscribe(subscription)
        logging.info('[SUBSCRIBED {}] mid {}, QOS: {}, properties {}'.format(
            client._client_id, mid, granted_qos, properties))


def assign_callbacks_to_client(client):
    # helper function which sets up client's callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

def sig_handler(signum, frame):
    signame = signal.Signals(signum).name
    sys.exit(1)

# KeyboardInterrupt
signal.signal(signal.SIGINT, sig_handler)
# Terminate signal
signal.signal(signal.SIGTERM, sig_handler)

async def main():
    # create client instance, kwargs (session expiry interval and maximum packet size)
    # will be send as properties in connect packet
    host = "localhost"
    port = 1883
    token = Token

    sub_client = gmqtt.Client("clientgonnasub")

    assign_callbacks_to_client(sub_client)
    sub_client.set_auth_credentials(AppID, token)

    await sub_client.connect(host, port)

    # two overlapping subscriptions with different subscription identifiers
    subscriptions = [
        gmqtt.Subscription('TEST/PROPS/#', qos=1),
        gmqtt.Subscription('TEST2/PROPS/#', qos=2),
    ]
    sub_client.subscribe(subscriptions, subscription_identifier=1)

    pub_client = gmqtt.Client("clientgonnapub")

    assign_callbacks_to_client(pub_client)
    pub_client.set_auth_credentials(AppID, token)
    await pub_client.connect(host, port)

    # this message received by sub_client will have two subscription identifiers
    pub_client.publish('TEST/PROPS/42', '42 is the answer', qos=1, content_type='utf-8',
                       message_expiry_interval=60, user_property=('time', str(time.time())))
    pub_client.publish('TEST2/PROPS/42', '42 is the answer', qos=1, content_type='utf-8',
                       message_expiry_interval=60, user_property=('time', str(time.time())))

    await asyncio.Event().wait()
    logging.info("test stoped")
    
    await pub_client.disconnect()
    await sub_client.disconnect(session_expiry_interval=0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
