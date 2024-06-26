import threading
from filip.models.ngsi_v2.iot import Device
import json
from typing import List
from socketinterface import SocketInterface
from mqttclient import MqttClient


class Socket2MQTT:
    """
    A gateway between simple socket transmission and MQTT (with fiware format)
    This gateway has two interfaces: a south bounded socketinterface and a
    north bounded mqttclient.

    The measurements and commands will be first cached in self.measurements and
    self.commands. Data flows of the two directions are handled by the two
    interfaces respectively.
    """
    def __init__(self):
        devices_path = "devices.json"  # load the devices
        with open(devices_path, "r") as f:
            devices_list = json.load(f)
        self.devices = [Device(**device) for device in devices_list]

        # initialize cache
        self.measurements = list()
        self.commands = list()

        # south bounded interface
        self.socket_interface = SocketInterface(self)
        self.mqtt_client = MqttClient(self)


if __name__ == '__main__':
    s2m = Socket2MQTT()

    t2 = threading.Thread(target=s2m.socket_interface.socket_server, daemon=False)
    t2.start()

    t1 = threading.Thread(target=s2m.mqtt_client.loop, daemon=False)
    t1.start()
