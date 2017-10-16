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
  if rc == 0:
      logging.info('Connected to MQTT broker')
      global connected
      connected = True
  else:
      logging.error('Connection to MQTT broker failed')

def on_message(client, userdata, message):
  global state
  if message.payload == b'not_home':
    logging.debug('Message received: presence = False (not_home)')
    presence = False
  if message.payload == b'home':
    logging.debug('Message received: presence = True (home)')
    presence = True

def bluetooth_ping():
  global presence
  for device, mac_address in config.presence_list.items():
      logging.debug('Starting l2ping for device: {}, MAC: {}'.format(device, mac_address))
      result = subprocess.call(["l2ping", "-c1", "-s32", "-t1", mac_address])
      if result == 0:
          client.publish(config.mqtt_topic_prefix + "/" + device, "home")
          presence = True

if __name__ == '__main__':
    logging.info('PyPresence starting')