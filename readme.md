## Solarman stick logger to mqtt


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