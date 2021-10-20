#!/usr/bin/python
"""InverterExport program.

Get data from a Wi-Fi kit logger and save/send the data to the defined plugin(s)
"""
import socket  # Needed for talking to logger
import time
import logging
import logging.config
import sys

if sys.version[:1] == '2':
    import ConfigParser as configparser
else:
    import configparser
import optparse
import os
import re
import InverterMsg  # Import the Msg handler
import InverterLib  # Import the library

# For MQTT
from datetime import datetime
import paho.mqtt.client as mqtt  # pip install paho-mqtt
import json


class SyncSolarMan:

    config = None
    logger = None

    ha_base_topic = "homeassistant"
    sensor_base_topic = "solarman"
    inverter_brand = "Waaree"
    inverter_model = "W1-4K-G3"

    def __init__(self, config_file):
        # Load the setting
        config_files = InverterLib.expand_path('config.cfg')

        self.config = configparser.RawConfigParser()
        self.config.read(config_files)

        self.logger_ip = self.config.get('logger', 'ip')
        self.logger_sn = self.config.get('logger', 'sn')
        self.logger_port = self.config.get('logger', 'port')
        self.inverter_brand = self.config.get('logger', 'inverter_brand')
        self.inverter_model = self.config.get('logger', 'inverter_model')

        self.mqtt_server = self.config.get('mqtt', 'host')
        self.mqtt_port = self.config.get('mqtt', 'port')
        self.mqtt_user = self.config.get('mqtt', 'user')
        self.mqtt_password = self.config.get('mqtt', 'password')

    def init_sensor(self, sensor_name, state_class, device_class, unit_of_measurement, client):

        payload = {
            "unit_of_measurement": unit_of_measurement,
            "name": self.inverter_brand+" "+sensor_name,
            "state_topic": self.sensor_base_topic+"/sensor/"+sensor_name+"/state",
            "availability_topic": self.sensor_base_topic+"/status",
            "unique_id": self.sensor_base_topic+"_"+sensor_name,
            "device": {
                "identifiers": self.inverter_model,
                "name": self.inverter_model,
                "sw_version": "1.0",
                "model": self.inverter_model,
                "manufacturer": self.inverter_brand
            }
        }

        if device_class != None:
            payload["device_class"] = device_class
        if state_class != None:
            payload["state_class"] = state_class

        client.publish(self.ha_base_topic +
                       '/sensor/'+self.sensor_base_topic+'/'+sensor_name+'/config', json.dumps(payload))
        

    def init_device(self):

        client = mqtt.Client("Solar Inverter")
        client.username_pw_set(self.mqtt_user, self.mqtt_password)
        client.connect(self.mqtt_server, int(self.mqtt_port), 60)

        # Power
        self.init_sensor('total_energy', 'total_increasing', 'energy', 'kWh',client)
        self.init_sensor('daily_energy', 'total_increasing', 'energy', 'kWh',client)
        self.init_sensor('total_hours', 'total_increasing', None, 'h',client)

        self.init_sensor('ac_power', 'measurement', 'power', 'kW',client)
        self.init_sensor('ac_frequency', "measurement", None, 'Hz',client)
        self.init_sensor('ac_current', 'measurement', 'current', 'A',client)
        self.init_sensor('ac_volage', 'measurement', 'voltage', 'V',client)

        # PV
        self.init_sensor('dc_current_1', 'measurement', 'current', 'A',client)
        self.init_sensor('dc_current_2', 'measurement', 'current', 'A',client)

        self.init_sensor('dc_voltage_1', 'measurement', 'voltage', 'V',client)
        self.init_sensor('dc_voltage_2', 'measurement', 'voltage', 'V',client)

        self.init_sensor('dc_power_1', 'measurement', 'power', 'Kw',client)
        self.init_sensor('dc_power_2', 'measurement', 'power', 'kw',client)

        # client.publish(self.sensor_base_topic+"/sensor/ac_power/state", msg.p_ac(1))
        # client.publish(self.sensor_base_topic+"/status", "online")

        client.loop(2)
        client.disconnect()

    def process_message(self, msg):
        
        client = mqtt.Client("Solar Inverter")
        client.username_pw_set(self.mqtt_user,
                               self.mqtt_password)
        client.connect(self.mqtt_server,
                       int(self.mqtt_port), 60)

        self.set_sensor_state(client, 'total_hours', msg.h_total)
        self.set_sensor_state(client, 'total_energy', msg.e_total)
        self.set_sensor_state(client, 'daily_energy', msg.e_today)

        self.set_sensor_state(client, 'ac_power', msg.p_ac(1))
        self.set_sensor_state(client, 'ac_frequency', msg.f_ac(1))
        self.set_sensor_state(client, 'ac_current', msg.i_ac(1))
        self.set_sensor_state(client, 'ac_volage', msg.v_ac(1))

        self.set_sensor_state(client, 'dc_power_1', msg.v_pv(1))
        self.set_sensor_state(client, 'dc_power_2', msg.v_pv(2))

        self.set_sensor_state(client, 'dc_voltage_1', msg.v_pv(1))
        self.set_sensor_state(client, 'dc_voltage_2', msg.v_pv(2))

        self.set_sensor_state(client, 'dc_current_1', msg.i_pv(1))
        self.set_sensor_state(client, 'dc_current_2', msg.i_pv(2))

    def set_sensor_state(self, client, sensor_name, state):
        client.publish(self.sensor_base_topic+"/sensor/" +
                       sensor_name+"/state", state)
        client.publish(self.sensor_base_topic+"/status", "online")

    def run(self):

        self.init_device()
        timeout = 3

        print('connecting to {0} port {1}'.format(
            self.logger_ip, self.logger_port))

        for res in socket.getaddrinfo(self.logger_ip, self.logger_port, socket.AF_INET, socket.SOCK_STREAM):
            family, socktype, proto, canonname, sockadress = res
            try:
                print('connecting to {0} port {1}'.format(
                    self.logger_ip, self.logger_port))
                logger_socket = socket.socket(family, socktype, proto)
                logger_socket.settimeout(timeout)
                logger_socket.connect(sockadress)
            except socket.error as msg:
                print('Could not open socket')
                next = True
                break

        data = InverterLib.createV5RequestFrame(int(self.logger_sn))
        response = []
        okflag = False
        while (not okflag):
            try:
                logger_socket.sendall(data)
            except socket.error as e:
                print('Connection error IP: {0} and SN {1}, trying next logger.'.format(
                    self.logger_ip, self.logger_port))
                continue
            try:
                response = logger_socket.recv(1024)
            except socket.timeout as e:
                print('Timeout connecting to logger with IP: {0} and SN {1}, trying next logger.'.format(
                    self.logger_ip, self.logger_port))
                continue

            if len(response) > 20:
                msg = InverterMsg.InverterMsg(response, self.logger)

            if (msg.msg)[:9] == 'DATA SEND':
                self.logger.debug("Exit Status: {0}".format(msg.msg))
                logger_socket.close()
                continue

            if (msg.msg)[:11] == 'NO INVERTER':
                self.logger.debug(
                    "Inverter(s) are in sleep mode: {0} received".format(msg.msg))
                logger_socket.close()
                continue

            print("Reading data from logger")

            self.process_message(msg)

            time.sleep(5)


if __name__ == "__main__":
    inverter_exporter = SyncSolarMan('config.cfg')
    inverter_exporter.run()
