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
import subprocess
import platform
import time
import datetime


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
        self.init_sensor('total_energy', 'total',
                         'energy', 'kWh', client)
        self.init_sensor('daily_energy', 'total_increasing',
                         'energy', 'kWh', client)
        self.init_sensor('total_hours', 'total', None, 'h', client)

        self.init_sensor('ac_power', 'measurement', 'power', 'kW', client)
        self.init_sensor('ac_frequency', "measurement", None, 'Hz', client)
        self.init_sensor('ac_current', 'measurement', 'current', 'A', client)
        self.init_sensor('ac_volage', 'measurement', 'voltage', 'V', client)

        # PV
        self.init_sensor('dc_current_1', 'measurement', 'current', 'A', client)
        self.init_sensor('dc_current_2', 'measurement', 'current', 'A', client)

        self.init_sensor('dc_voltage_1', 'measurement', 'voltage', 'V', client)
        self.init_sensor('dc_voltage_2', 'measurement', 'voltage', 'V', client)

        self.init_sensor('dc_power_1', 'measurement', 'power', 'kW', client)
        self.init_sensor('dc_power_2', 'measurement', 'power', 'kW', client)

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

        sensors = [
            {"name": "total_hours", "value": msg.h_total},
            {"name": "total_energy", "value": msg.e_total},
            {"name": "daily_energy", "value": msg.e_today},

            {"name": "ac_power", "value": "{:.2f}".format(msg.p_ac(1))},
            {"name": "ac_frequency", "value": msg.h_total},
            {"name": "ac_current", "value": msg.i_ac(1)},
            {"name": "ac_volage", "value": msg.v_ac(1)},

            {"name": "dc_power_1", "value": msg.p_pv(1)},
            {"name": "dc_power_2", "value": msg.p_pv(2)},

            {"name": "dc_voltage_1", "value": msg.v_pv(1)},
            {"name": "dc_voltage_2", "value": msg.v_pv(2)},

            {"name": "dc_current_1", "value": msg.i_pv(1)},
            {"name": "dc_current_2", "value": msg.i_pv(2)}
        ]
        ## Should not be zero e_today and h_total
        if float(msg.e_today) != 0.0 and float(msg.h_total) != 0.0:
            for sensor in sensors:
                self.set_sensor_state(client, sensor['name'], sensor['value'])
        else:
            self.logMessage('Invalid value for total value')

        # inf = InfluxDB(self.logger_sn)
        # inf.store(sensors)

    def set_sensor_state(self, client, sensor_name, state):

        client.publish(self.sensor_base_topic+"/sensor/" +
                       sensor_name+"/state", state)
        client.publish(self.sensor_base_topic+"/status", "online")

    def set_device_status(self, status):
        client = mqtt.Client("Solar Inverter")
        client.username_pw_set(self.mqtt_user,
                               self.mqtt_password)
        client.connect(self.mqtt_server,
                       int(self.mqtt_port), 60)
        client.publish(self.sensor_base_topic+"/status", status)

    def check_device_online(self, sHost):
        try:
            output = subprocess.check_output("ping -{} 1 {}".format(
                'n' if platform.system().lower() == "windows" else 'c', sHost), shell=True)
        except Exception as e:
            return False
        return True

    def logMessage(self, msg):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        file = open('logs/run.log', 'a+')
        file.write('{} : {}\n'.format(st, msg))
        file.close()

    def opensocket(self):
        for res in socket.getaddrinfo(self.logger_ip, self.logger_port, socket.AF_INET, socket.SOCK_STREAM):
            family, socktype, proto, canonname, sockadress = res
            try:
                self.logMessage('connecting to {0} port {1}'.format(
                    self.logger_ip, self.logger_port))
                logger_socket = socket.socket(family, socktype, proto)
                logger_socket.settimeout(10)
                logger_socket.connect(sockadress)
                return logger_socket
            except socket.error as msg:
                self.logMessage('Could not open socket, aborting ')
        # self.set_device_status('offline')
        # exit(1)

    def run(self):
        data = InverterLib.createV5RequestFrame(int(self.logger_sn))
        response = []
        last_offline = True
        while (1):

            if(last_offline):
                self.init_device()
                logger_socket = self.opensocket()

            if(not logger_socket or not self.check_device_online(self.logger_ip)):
                self.logMessage('Device at {} offline. Waiting 20s before retry . '.format(
                    self.logger_ip))
                self.set_device_status('offline')
                time.sleep(20)
                last_offline = True
                continue

            try:
                logger_socket.sendall(data)
            except socket.error as e:
                self.logMessage('Connection error IP: {0} and SN {1}, trying next logger.'.format(
                    self.logger_ip, self.logger_port))
                last_offline = True
                continue
            try:
                response = logger_socket.recv(1024)
            except socket.timeout as e:
                self.logMessage('Timeout connecting to logger with IP: {0} and SN {1}, trying next logger.'.format(
                    self.logger_ip, self.logger_port))
                continue

            if len(response) > 20:
                msg = InverterMsg.InverterMsg(response, self.logger)

            if (msg.msg)[:9] == 'DATA SEND':
                self.logMessage("Exit Status: {0}".format(msg.msg))
                logger_socket.close()
                continue

            if (msg.msg)[:11] == 'NO INVERTER':
                self.logMessage(
                    "Inverter(s) are in sleep mode: {0} received".format(msg.msg))
                logger_socket.close()
                continue

            self.logMessage("Reading data from logger")
            self.set_device_status('online')
            self.process_message(msg)
            time.sleep(10)


if __name__ == "__main__":
    inverter_exporter = SyncSolarMan('config.cfg')
    inverter_exporter.run()
