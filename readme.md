## Introduction

![ha-dash](https://user-images.githubusercontent.com/693151/138284713-34f78fee-0b73-47e0-8f42-23bc204a9e5d.JPG)


Solarman to MQTT a small script to get data from Omnik, Hosola, Goodwe, Solax, Ginlong, Samil, Sofar or Power-One Solar inverter, equipped with a wifi module or connected to a Wi-Fi data logger and push to an mqtt server of your choice.

MQTT topic optimized for Home Assistant [autodiscovery](https://www.home-assistant.io/docs/mqtt/discovery/).

This script is adapted from  [https://github.com/mcikosos/Inverter-Data-Logger](https://github.com/mcikosos/Inverter-Data-Logger)

Check the above link to know the list of supported inverters.

## Notes

This service should be running on an always on device preferably a Raspberry Pi or a VM.

Wifi Logger needs a static ip inorder to work flawlessly [https://www.pcmag.com/how-to/how-to-set-up-a-static-ip-address](https://www.pcmag.com/how-to/how-to-set-up-a-static-ip-address) 

<img src="https://user-images.githubusercontent.com/693151/138283943-fdee03e0-bf31-4658-9ae8-25576b1819b9.png" data-canonical-src="https://user-images.githubusercontent.com/693151/138283943-fdee03e0-bf31-4658-9ae8-25576b1819b9.png" width="200"  />

## Solarman stick logger to mqtt

`git clone https://github.com/arevindh/solarman-to-mqtt`

`cd solarman-to-mqtt`

`cp config.org.cfg config.cfg`

Edit the contents to match your settings

## Install requirements 

`pip3 install -r requirements.txt`

## Testing

`python3 SyncSolarMan.py`

## Create Service 

Change `dietpi` to your username ( `whoami` will provide you with your username )

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


## To do

- Better handling of offline device
- Code refactor
