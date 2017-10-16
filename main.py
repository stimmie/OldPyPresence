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
    logging.debug('In function')
    if rc == 0:
        logging.info('Connected to MQTT broker')
        global connected
        connected = True
    else:
        logging.error('Connection to MQTT broker failed')

def on_message(client, userdata, message):
    logging.debug('Received a message')
    global state
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
        result = subprocess.call(['l2ping', '-c1', '-s32', '-t1', mac_address], stdout=DEVNULL, stderr=DEVNULL)
        if result == 0:
            logging.debug('Device: {}, MAC: {} is responding'.format(device, mac_address))
            client.publish(config.mqtt_topic_prefix + '/' + device, 'home')
            presence = True

if __name__ == '__main__':
    logging.info('PyPresence starting')
    client = mqttClient.Client(config.mqtt_client_name)
    client.username_pw_set(config.broker_username, password=config.broker_password)
    client.on_connect = on_connect
    client.on_message = on_message
    logging.debug('Calling client connect')
    client.connect(config.broker_ip, port=config.broker_port)
    logging.debug('Client start loop')
    client.loop_start()
    while connected != True:
        logging.debug('In main while loop')
        time.sleep(0.1)
        client.subscribe(config.mqtt_topic_prefix + '/' + config.mqtt_listening_topic)
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