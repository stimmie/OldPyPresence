#!/usr/bin/env python3

import time
import config
import logging
import paho.mqtt.client as mqttClient
import subprocess

logging.basicConfig(
    level=config.log_level,
    format=config.log_format
    )

presence = False
connected = False

def on_connect(client, userdata, flags, rc):
    logging.debug('Entered the function on_connect')
    if rc == 0:
        logging.info('Connected to MQTT broker')
        logging.debug('Subscribing to MQTT topic: {}/{}'.format(config.mqtt_topic_prefix, config.mqtt_listening_topic))
        client.subscribe(config.mqtt_topic_prefix + '/' + config.mqtt_listening_topic)
        global connected
        connected = True
    else:
        logging.error('Connection to MQTT broker failed')

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.error('Unexpected MQTT disconnection, will auto-reconnect')

def on_message(client, userdata, message):
    logging.debug('Received a message')
    global presence
    if message.payload == b'not_home':
        logging.debug('Message received: presence = False (not_home)')
        presence = False
    if message.payload == b'home':
        logging.debug('Message received: presence = True (home)')
        presence = True

def bluetooth_ping():
    logging.debug('Starting bluetooth l2ping')
    global presence
    for device, mac_address in config.presence_list.items():
        logging.debug('Starting l2ping for device: {}, MAC: {}'.format(device, mac_address))
        result = subprocess.run(
            ['l2ping', '-c1', '-s32', '-t1', mac_address],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL
            )
        if result.returncode == 0:
            logging.debug('Device: {}, MAC: {} is responding'.format(device, mac_address))
            logging.debug('Sending message: home in topic: {}/{}'.format(config.mqtt_topic_prefix, device))
            client.publish(config.mqtt_topic_prefix + '/' + device, 'home')
            presence = True

def connect_to_broker():
    global client
    client = mqttClient.Client(config.mqtt_client_name)
    client.username_pw_set(config.broker_username, password=config.broker_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    logging.debug('Connecting to MQTT broker')
    client.connect(config.broker_ip, port=config.broker_port)
    logging.debug('Starting MQTT client loop')
    client.loop_start()

if __name__ == '__main__':
    logging.info('PyPresence starting')
    connect_to_broker()
    while connected != True:
        logging.debug('Main loop starting')
        time.sleep(0.1)
        try:
            while True:
                logging.debug('Sleep 5 seconds')
                time.sleep(5)
                if presence == False:
                    logging.debug('Presence is False calling bluetooth_ping()')
                    bluetooth_ping()
        except KeyboardInterrupt:
            logging.info('PyPresence exiting')
            client.disconnect()
            client.loop_stop()