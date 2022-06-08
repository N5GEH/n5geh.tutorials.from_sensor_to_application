"""
TODO
 This script is currently not used.
"""
import os
import threading
import time
import json
import socket
from filip.clients.mqtt import IoTAMQTTClient
from filip.clients.ngsi_v2 import IoTAClient
from filip.models.base import FiwareHeader
from filip.models.ngsi_v2.iot import PayloadProtocol
import paho.mqtt.client as mqtt
from uuid import uuid4
# TODO the device should be marked by a URN, which can hopefully
#  represents the most common cases dvice_id = uuid4()
MQTT_HOST = "host.docker.internal"


class Transducer:
    def __init__(self):
        # TODO may need change or get from ENV
        IOTA_URL = os.getenv("IOTA_URL", "http://localhost:4041")
        # TODO how to get these information
        # FIWARE-Service
        SERVICE = "controller"
        # FIWARE-Servicepath
        SERVICE_PATH = "/"
        # API key of the devices group
        APIKEY = "n5gehtutorial"

        fiware_header = FiwareHeader(service=SERVICE,
                                     service_path=SERVICE_PATH)

        iotac = IoTAClient(url=IOTA_URL, fiware_header=fiware_header)

        # TODO device information (manually input or load an input data)
        #  I dont like to get the device information from the platform
        #  It will be great, when device information can be exported from SENSE/Entirety as JSON-file
        self.weather_station = iotac.get_device(device_id="device:001")
        self.zone_temperature_sensor = iotac.get_device(device_id="device:002")
        self.heater = iotac.get_device(device_id="device:003")

        # initialize sensor and actuator data
        self.heaterPower = None
        self.temp_amb = None
        self.temp_zone = None

        # TODO Get the service group configurations from the server
        #  It also should be exported from the SENSE
        group = iotac.get_group(resource="/iot/json", apikey=APIKEY)
        self.mqttc = IoTAMQTTClient(protocol=mqtt.MQTTv5,
                                    devices=[self.weather_station,
                                             self.zone_temperature_sensor,
                                             self.heater],
                                    service_groups=[group])

    def mqtt_client(self):
        def on_command(client, obj, msg):
            """
            Callback for incoming commands
            """
            # Decode the message payload using the libraries builtin encoders
            apikey, device_id, payload = \
                client.get_encoder(PayloadProtocol.IOTA_JSON).decode_message(
                    msg=msg)
            # Update the heating power of the simulation model
            self.heaterPower = float(payload["heaterPower"])
            print(f"receive command {self.heaterPower}")

            # Acknowledge the command (necessary!)
            client.publish(device_id=device_id,
                           command_name=next(iter(payload)),
                           payload=payload)

        # add command call back
        self.mqttc.add_command_callback(device_id=self.heater.device_id,
                                        callback=on_command)
        print(f"Try to connect with {MQTT_HOST, 1883}", flush=True)

        # try:
        self.mqttc.connect(host=MQTT_HOST, port=1883)
        # except Exception as e:
        #     print(e)
        #     raise

        # subscribe to all incoming command topics for the registered devices
        print(f"Try to subscribe", flush=True)
        self.mqttc.subscribe()
        print(f"Loop start", flush=True)
        self.mqttc.loop_start()

        try:
            while True:
                print("loop mqtt", flush=True)
                # send measurement
                self.mqttc.publish(device_id=self.weather_station.device_id,
                                   payload={"temperature": self.temp_amb})
                self.mqttc.publish(device_id=self.zone_temperature_sensor.device_id,
                                   payload={"temperature": self.temp_zone})
                time.sleep(0.5)
        except Exception as e:
            print(e, flush=True)
        finally:
            self.mqttc.loop_stop()
            self.mqttc.disconnect()

    def socket_server(self):
        # get the hostname
        host = socket.gethostname()
        port = 5000  # initiate port no above 1024

        server_socket = socket.socket()  # get instance
        server_socket.settimeout(2)  # TODO 1 second time out
        # look closely. The bind() function takes tuple as argument
        server_socket.bind((host, port))  # bind host address and port together

        # configure how many client the server can listen simultaneously
        server_socket.listen(2)

        while True:
            print("loop socket", flush=True)
            try:
                conn, address = server_socket.accept()  # accept new connection
                print("Connection from: " + str(address), flush=True)

                # read measurements from sensors
                measurements = conn.recv(1024).decode()
                print("from connected client: " + str(measurements), flush=True)
                measurements = dict(json.loads(measurements))  # TODO default data format {"temp_amb": 111, "temp_zone": 222}
                self.temp_amb = float(measurements.get("temp_amb"))
                self.temp_zone = float(measurements.get("temp_zone"))

                # send commands to actuators
                if isinstance(self.heaterPower, (float, int)):
                    commands = json.dumps({"heaterPower": self.heaterPower})
                    conn.send(commands.encode())  # send data to the client
                conn.close()
            except socket.timeout:
                # TODO do what when time out?
                pass


if __name__ == '__main__':
    transducer = Transducer()

    t2 = threading.Thread(target=transducer.socket_server, daemon=False)
    t2.start()

    t1 = threading.Thread(target=transducer.mqtt_client, daemon=False)
    t1.start()
