import os
import time
from filip.clients.mqtt import IoTAMQTTClient
from filip.models.ngsi_v2.iot import PayloadProtocol
import paho.mqtt.client as mqtt


class MqttClient:
    """
    The MQTT interface that send measurements to and receive
    commands from the MQTT broker of FIWARE.
    """
    def __init__(self, gateway):
        self.gateway = gateway
        self.mqttc = IoTAMQTTClient(protocol=mqtt.MQTTv5,
                                    devices=self.gateway.devices)
                                    # service_groups=[group])
                                    # The service group is only relevant for auto provisioning
        self.create_callback()
        self.mqtt_host = os.getenv("MQTT_HOST", "host.docker.internal")
        # self.mqtt_host = "localhost"
        self.mqtt_port = int(os.getenv("MQTT_PORT", 1883))

    def create_callback(self):
        """
        Add on command call back for all devices that have at least
        one command attribute.
        """
        for device in self.gateway.devices:
            if device.commands:
                def on_command(client, obj, msg):
                    """
                    Callback function for incoming commands
                    """
                    # Decode the message payload using the libraries builtin encoders
                    apikey, device_id, payload = \
                        client.get_encoder(PayloadProtocol.IOTA_JSON).decode_message(
                            msg=msg)

                    # Transfer the command to the wanted format
                    command_dict = {device_id: dict(payload)}

                    # Add the command in the commands list
                    self.gateway.commands.append(command_dict)
                    print(f"receive command {command_dict}", flush=True)

                    # Acknowledge the command (necessary!)
                    client.publish(device_id=device_id,
                                   command_name=next(iter(payload)),
                                   payload=payload)
                # add command call back
                self.mqttc.add_command_callback(device_id=device.device_id,
                                                callback=on_command)
            else:
                # do nothing if the device does not have any command
                continue

    def loop(self):
        """
        The main loop of MQTT client, which listen to the command and send measurement
        to the Iot Agent
        """
        self.mqttc.connect(host=self.mqtt_host, port=self.mqtt_port)
        self.mqttc.subscribe()
        print(f"MQTT loop start", flush=True)

        self.mqttc.loop_start()
        try:
            while True:
                # add a small sleep time, otherwise this thread will block the other threads
                time.sleep(0.05)
                if self.gateway.measurements:
                    # TODO send measurement, one measurements at a time?
                    # format of measurement {"device_id": {"attribute_name": "value"}}
                    measurement = self.gateway.measurements.pop(0)
                    device_id, payload = list(measurement.items())[0]
                    print(f"send mqtt {device_id}: {payload}", flush=True)
                    self.mqttc.publish(device_id=device_id,
                                       payload=payload)
        except Exception as e:
            print("MQTT client failure", flush=True)
            raise e
        finally:
            self.mqttc.loop_stop()
            self.mqttc.disconnect()
