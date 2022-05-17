"""
Simulation model to provide dynamic data throughout the tutorial
"""
from math import cos
import numpy as np


class SimulationModel:
    """
    Simulation model for a thermal zone and periodic ambient temperature
    simulation.

    The ambient temperature is simulated as daily periodic cosine ranging
    between `temp_max` and `temp_min`.

    The thermal zone is roughly parametrized as follows:
    Zone volume: 10m x 10m x 5m
    Outer wall area plus roof ares: 4 x 10m x 5m + 10m x 10m
    Thermal insulation factor U: 0.4 W/(m^2 K)

    Args:
        t_start: simulation start time in seconds
        t_end: simulation end time in seconds
        dt: model integration step in seconds
        temp_max: maximal ambient temperature in °C
        temp_min: minimal ambient temperature in °C
        temp_start: initial zone temperature in °C
    """

    def __init__(self,
                 t_start: int = 0,
                 t_end: int = 24 * 60 * 60,
                 dt: int = 1,
                 temp_max: float = 10,
                 temp_min: float = -5,
                 temp_start_amb: float = -5,
                 temp_start_zone: float = 20,
                 temp_start_heater: float = 20,
                 heat_power_start: float = 2000):
        self.t_start = t_start
        self.t_end = t_end
        self.dt = dt
        self.temp_max = temp_max
        self.temp_min = temp_min
        self.ua = 120
        self.heat_transfer_heater = 100
        self.c_p = 612.5 * 100
        self.c_p_heater = 0.2 * self.c_p  # heat capacity of the heater
        self.q_h = heat_power_start  # heating power
        self.t_sim = self.t_start
        self.t_amb = temp_start_amb
        self.t_zone = temp_start_zone
        self.t_heater = temp_start_heater
        self.on_off: bool = True  # always turn on

    # define the function that returns a virtual ambient temperature depend from the
    # the simulation time using cosinus function
    def do_step(self, t_sim: int):
        """
        Performs a simulation step of length `t_sim`

        Args:
            t_sim: simulation step in seconds

        Returns:
            t_sim: simulation step end time in seconds
            t_amb: ambient temperature in °C
            t_zone: zone temperature in °C
        """
        for t in range(self.t_sim, t_sim, self.dt):

            self.t_heater = self.t_heater + \
                            self.dt * (self.heat_transfer_heater * (self.t_zone - self.t_heater) +
                                       self.on_off * self.q_h) / self.c_p_heater

            self.t_zone = self.t_zone + \
                          self.dt * (self.ua * (self.t_amb - self.t_zone) +
                                     self.heat_transfer_heater * (self.t_heater - self.t_zone)) / self.c_p

            self.t_amb = -(self.temp_max - self.temp_min) / 2 * \
                         cos(2 * np.pi * t / (24 * 60 * 60)) + \
                         self.temp_min + (self.temp_max - self.temp_min) / 2

        self.t_sim = t_sim

        return self.t_sim, self.t_amb, self, self.t_zone

    @property
    def heater_power(self):
        """
        Returns heating power in [W]
        """
        return self.q_h

    @heater_power.setter
    def heater_power(self, power: [int, float]):
        """
        Sets heating power

        Args:
            power: heater power in [W]
        """
        q_h = float(power)
        self.q_h = q_h
