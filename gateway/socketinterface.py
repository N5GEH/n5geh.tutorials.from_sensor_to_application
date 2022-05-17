import socket
import json
import threading
from utils import reverse_mapping

# load mapping and reverse mapping
path_mapping = "mapping.json"
with open(path_mapping, "r") as f:
    mapping = json.load(f)  # mapping from urn to device id
    mapping_rev = reverse_mapping(mapping)  # mapping from device id to urn


class SocketInterface:
    """
    The interface that handle the data transmission directly with
    the devices. In this tutorial, the transmission protocol is socket.
    """
    def __init__(self, gateway):
        self.gateway = gateway

    def socket_server(self):
        """
        Start the socket server that waiting for the connection from
        socket clients.
        """
        # get the local hostname
        host = socket.gethostname()
        port = 5000  # initiate port no above 1024

        server_socket = socket.socket()  # get instance
        server_socket.settimeout(1)

        # look closely. The bind() function takes tuple as argument
        print(f"host: {socket.gethostbyname(host)}", flush=True)
        server_socket.bind((host, port))  # bind host address and port together

        # configure how many client the server can listen simultaneously
        server_socket.listen(2)

        while True:
            print("loop socket", flush=True)
            try:
                conn, address = server_socket.accept()  # accept new connection
                print(f"new connection received: {address}", flush=True)
                t = threading.Thread(target=self.client_handler, args=(conn, address), daemon=False)
                t.start()
            except socket.timeout:
                print("client connection time out")

    def client_handler(self, _conn, _address):
        """
        Handler for the socket communication.

        A flag should be received before any communication start, which
        is used to identify, whether data should be sent or received.
        """
        flag = _conn.recv(1024).decode()
        print(f"flag: {flag}", flush=True)
        if flag == "MEASUREMENT":
            measurements = _conn.recv(1024).decode()
            measurements_dicts = self.parse2dict(measurements)
            print(f"measurements: {measurements_dicts}", flush=True)
            # multiple measurements will be sent together
            self.gateway.measurements += measurements_dicts
        elif flag == "COMMAND":
            if self.gateway.commands:
                commands_dict = self.gateway.commands.pop(0)  # forward one command at a time
                commands = self.parse_from_dict(commands_dict)
                _conn.send(commands.encode())
            else:
                _conn.send("".encode())
        _conn.close()

    @staticmethod
    def parse2dict(measurements: str) -> list:
        """
        Parse the measurements strings that received from devices
        into the format of the measurement cache.

        From:  {outer_temp_sensor_urn: "value",
                inner_temp_sensor_urn: "value"}

        To:  {"device_id": {"attribute_name": "value"}}

        :param measurements: json strings
                            e.g. '{"urn1/urn2": "value","urn1/urn2": "value"}'
        :return: list of dict
                e.g. [{"device_id_1": {"attribute_name": "value"}},
                      {"device_id_2": {"attribute_name": "value"}}]
        """
        measurements_list = []
        measurements = json.loads(measurements)
        for urn in measurements:
            urn1, urn2 = urn.split("/")  # connection card can be changed or ignored
            value = measurements[urn]
            measurement_dict = {
                mapping[urn1]["device_id"]: {
                    mapping[urn1]["attribute/command"][urn2]: value
                    }
            }
            measurements_list.append(measurement_dict)
        return measurements_list

    @staticmethod
    def parse_from_dict(commands_dict: dict) -> str:
        """
        Parse the measurements strings that received from devices
        into the format of the measurement cache.

        From:  {outer_temp_sensor_urn: "value",
                inner_temp_sensor_urn: "value"}

        To:  {"device_id": {"attribute_name": "value"}}

        :param commands_dict: dict from commands cache
                            e.g. {"device_id": {"command_name": "value"}}
        :return: json strings
                e.g. '{"urn1/urn2": "value"}'

        """
        device_id, attribute_value = list(commands_dict.items())[0]
        attribute_name, value = list(attribute_value.items())[0]

        urn_1 = mapping_rev[device_id]["urn"]
        urn_2 = mapping_rev[device_id]["attribute/command"][attribute_name]["urn"]
        urn = urn_1 + "/" + urn_2
        commands = {urn: value}
        commands = json.dumps(commands)
        return commands
