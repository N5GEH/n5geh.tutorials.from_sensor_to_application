import os
import threading

from SimulationModel import SimulationModel
import time
import PySimpleGUIWeb as sg
import socket
import json
import multiprocessing

# URN of each device and its attributes
# Here the URNs tend to emulate the real situation in any transmission protocol
outer_temp_sensor_urn = "c006d64e-69b2"  # weather station
outdoor_temp_urn = ""  # urn for attribute name

inner_temp_sensor_urn = "ddad85db-3873"  # zone temperature sensor
indoor_temp_urn = ""  # urn for attribute name

heater_urn = "0e83dd93-ba49"
heater_power_urn = ""  # urn for command name


class Simulation:
    def __init__(self,
                 TEMPERATURE_MAX=10,  # maximal ambient temperature
                 TEMPERATURE_MIN=-5,  # minimal ambient temperature
                 TEMPERATURE_ZONE_START=5,  # start value of the zone temperature
                 T_SIM_START=0,  # simulation start time in seconds
                 T_SIM_END=24 * 60 * 60,  # simulation end time in seconds
                 COM_STEP=60 * 15,  # 15 min communication step in seconds
                 SLEEP_TIME=0.5  # sleep time between every simulation step
                 ):

        self.COM_STEP = COM_STEP  # 1 min communication step in seconds
        self.SLEEP_TIME = SLEEP_TIME  # sleep time between every simulation step

        # Initial condition for simulation
        self.sim_model = SimulationModel(
            t_start=T_SIM_START,
            t_end=T_SIM_END,
            temp_max=TEMPERATURE_MAX,
            temp_min=TEMPERATURE_MIN,

            temp_start_zone=TEMPERATURE_ZONE_START,
            temp_start_heater=TEMPERATURE_ZONE_START,
            temp_start_amb=TEMPERATURE_MIN,  # degree C
            heat_power_start=2000,  # kw hard coded
        )

        self.gateway_host = os.getenv("GATEWAY_HOST", "gateway")
        self.gateway_port = int(os.getenv("GATEWAY_PORT", 5000))

        # initialize gui window
        sg.theme("DarkBlue3")

        # image file path
        path_weather = "./figures/Sun_bw.png"
        path_zone = "./figures/BLDG_bw.png"
        path_heater = "./figures/EH_bw.png"

        # set the gui layout
        fig_h = 3
        fig_w = fig_h * 2.8
        image_weather = sg.Image(filename=path_weather, key="image_w", size=(fig_w, fig_h))
        image_zone = sg.Image(filename=path_zone, key="image_z", size=(fig_w, fig_h))
        image_heater = sg.Image(filename=path_heater, key="image_h", size=(fig_w, fig_h))

        layout = [
            [sg.Text("Simulation Time: "), sg.Text("00:00:00", size=(15, 2), key="simulation_time")],
            [sg.Text("", size=(15, 2))],

            [image_weather, sg.Text("Ambient Temperature", size=(15, 3)),
             sg.Text(self.sim_model.t_amb, key="temp_amb"), sg.Text(f" ºC")],
            [sg.Text("", size=(15, 2))],

            [image_zone, sg.Text("Zone Temperature", size=(15, 3)),
             sg.Text(self.sim_model.t_zone, key="temp_zone"), sg.Text(f" ºC")],
            [sg.Text("", size=(15, 2))],

            [image_heater, sg.Text("Heater", size=(15, 3)),
             sg.Text(self.sim_model.heater_power, key="heating_power"), sg.Text(f" W"),
             sg.InputText("Heater Power", key="heating_power_change", size=(7, 1)), sg.Button("Change", key="CHANGE")],
            [sg.Text("", size=(15, 2))],

        ]
        self.window = sg.Window("Simulation", layout, web_port=8000, web_start_browser=True)

    def gui_event(self):
        """Check web GUI event"""
        event, values = self.window.read(timeout=100)
        print(f"event: {event}")
        if event in (sg.TIMEOUT_EVENT, None):
            pass
        elif event == "CHANGE":
            print("Change heating power", flush=True)
            try:
                heater_power = float(values["heating_power_change"])
                self.sim_model.heater_power = heater_power
            except ValueError:
                print("Wrong value type of heater power", flush=True)

    def gui_update(self):
        """Update the shown text on web GUI"""
        # update parameter values
        self.window["temp_amb"].update(round(self.sim_model.t_amb, 1))
        self.window["temp_zone"].update(round(self.sim_model.t_zone, 1))
        self.window["heating_power"].update(round(self.sim_model.heater_power, 1))
        sim_time_h = str(int(self.sim_model.t_sim // (60*60)))
        if len(sim_time_h) < 2:
            sim_time_h = "0" + sim_time_h

        sim_time_m = str(int(self.sim_model.t_sim % (60*60) // 60))
        if len(sim_time_m) < 2:
            sim_time_m = "0" + sim_time_m

        sim_time_s = str(int(self.sim_model.t_sim % 60))
        if len(sim_time_s) < 2:
            sim_time_s = "0" + sim_time_s

        self.window["simulation_time"].update(f"{sim_time_h}:{sim_time_m}:{sim_time_s}")

    def main_loop(self):
        """
        Loop of the simulation. The GUI event will be executed everytime and the
        simulation results will be sent over simple socket transmission.
        """
        while True:
            for t_sim in range(self.sim_model.t_start,
                               self.sim_model.t_end + int(self.COM_STEP),
                               int(self.COM_STEP)):
                # simulation step for next loop
                self.sim_model.do_step(int(t_sim + self.COM_STEP))

                # change the heater power from GUI
                self.gui_event()

                # update the data on gui
                self.gui_update()

                # wait for some time before calculate the next step
                time.sleep(self.SLEEP_TIME)

    def socket_loop(self):
        """
        send or get data via socket
        """
        while True:
            try:
                # check the availability of the host
                p = multiprocessing.Process(target=socket.gethostbyname,
                                            args=(self.gateway_host,),
                                            daemon=False)
                p.start()
                p.join(0.5)  # 0.5 sec works for most cases
                if p.is_alive():
                    # If the above thread did not finish in 1 second, the host
                    # is most likely to be unreachable
                    print("host name invalid")
                    p.terminate()
                    raise socket.timeout
                else:
                    self.socket_send()
                    self.socket_receive()
            except socket.timeout:
                print("Socket client connection timeout", flush=True)
            except Exception as e:
                print(e.args, flush=True)
            time.sleep(self.SLEEP_TIME)

    def socket_send(self):
        """
        Send measurements via socket
        """
        # print(f"try to connect with {(self.gateway_host, self.gateway_port)}", flush=True)
        client_socket = socket.socket()  # instantiate
        client_socket.settimeout(0.01)
        client_socket.connect((self.gateway_host, self.gateway_port))  # connect to the server

        # print("connected, and try to send measurements", flush=True)
        client_socket.send("MEASUREMENT".encode())  # send measurement flag

        time.sleep(0.01)  # wait until the flag has been received

        # send the measurements with the right urn
        measurements = json.dumps(
            {(outer_temp_sensor_urn + "/" + outdoor_temp_urn): self.sim_model.t_amb,
             (inner_temp_sensor_urn + "/" + indoor_temp_urn): self.sim_model.t_zone}
        )
        client_socket.send(measurements.encode())  # send measurement
        # print(f"sent: {measurements}")

    def socket_receive(self):
        """
        Get commands via socket
        """
        client_socket = socket.socket()  # instantiate
        client_socket.settimeout(0.01)
        client_socket.connect((self.gateway_host, self.gateway_port))  # connect to the server

        client_socket.send("COMMAND".encode())  # receive command flag

        # format of the command {"URN/URN": value}
        command = client_socket.recv(1024).decode()  # receive command

        if command:
            print(f"command: {command}", flush=True)
            command = dict(json.loads(command))
            urn = heater_urn + "/" + heater_power_urn
            self.sim_model.heater_power = float(command.get(urn))
        client_socket.close()  # close the connection


if __name__ == '__main__':
    simulation = Simulation(COM_STEP=60 * 15)

    thread = threading.Thread(target=simulation.socket_loop, daemon=False)
    thread.start()

    simulation.main_loop()
