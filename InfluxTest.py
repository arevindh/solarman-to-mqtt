from influxdb_client import InfluxDBClient


class InfluxDB():
    def __init__(self) -> None:
        self.client = InfluxDBClient(url="http://localhost:9999", token=token, org=org)
    
    def store(self):
        write_api = self.client.write_api()

if __name__ == "__main__":
    influx = InfluxDB('config.cfg')
    influx.save()
