## Introduction

Solarman to MQTT a small script to get data from Omnik, Hosola, Goodwe, Solax, Ginlong, Samil, Sofar or Power-One Solar inverter, equipped with a wifi module or connected to a Wi-Fi data logger and push to an mqtt server of your choice.

MQTT topic optimized for Home Assistant [autodiscovery](https://www.home-assistant.io/docs/mqtt/discovery/).

This script is adapted from  [https://github.com/silvester747/Inverter-Data-Logger](https://github.com/silvester747/Inverter-Data-Logger)

Check the above link to know the list of supported inverters.

## Solarman stick logger to mqtt

`git clone https://github.com/arevindh/solarman-to-mqtt`

`cd solarman-to-mqtt`

`cp config.org.cfg config.cfg`

Edit the contents to match your settings

## Install requirements 

pip3 install -r requirements.txt

## Testing

python3 SyncSolarMan.py

## Create Service 

`sudo nano /etc/systemd/system/solarman.service`

```
[Unit]
Description = Solarman Logger to MQTT
After = network.target

[Service]
Type = simple
ExecStart = python3 /home/dietpi/solarman-to-mqtt/SyncSolarMan.py
WorkingDirectory = /home/dietpi/solarman-to-mqtt
User = dietpi
Group = dietpi
Restart = on-failure
RestartSec = 60
TimeoutStartSec = infinity

[Install]
WantedBy = multi-user.target
```

`sudo systemctl daemon-reload`

`sudo systemctl start solarman`

`sudo systemctl status solarman`

`sudo systemctl enable solarman`