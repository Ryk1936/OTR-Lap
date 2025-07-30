# July 26th 2025
# Author: Ryan Koo - Ontario Tech Racing
# Description: Vehicle modelling. Generates a GGV plot for the LTS algorithm.
# Dependencies: pandas and openpyxl need to be installed for xlsx file reading.

# Notes: The directory holding parameter.xlsx and motor_curve.xlsx must have the same name as
#        the name value in the 2nd row of parameter.xlsx.


import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

# TEMPORARY PREFERENCES
np.set_printoptions(precision=2, suppress=True)  # Improves readability of values when debugging
dv = 0.5 / 3.6   # m/s step (0.5 km/h). Need to look into this further. Value taken from OpenLAP
# ^^^ Vehicle velocity mesh step size

class Vehicle:

    # Loaded in Vehicle Parameters
    name: str  # name of vehicle
    m: float  # mass of vehicle [kg]
    d_fm: float  # front mass distribution [%]
    Cl: float  # lift coefficent
    Cd: float  # drag coefficent
    d_fa: float  # front aero distribution [%]
    A: float  # frontal area [m^2]
    rho: float  # air density [kg/m^3]
    drive_type: str  # FWD, RWD or AWD
    fdr:  float  # final drive ratio
    tire_d: float  # tire diameter [in]
    tire_w: float  # tire width [in]
    tire_roll: float  # tire rolling radius / effective radius
    mu_x: float  # tire coefficent of friction longitudinal
    mu_y: float  # tire coefficent of friction lateral
    Crr: float  # rollling resistance coefficent

    # Calculated Vehicle Parameters
    num_dw: int  # number of driven wheels
    f_drive: float
    f_aero: float

    # Forces and Velocity (GGV Plot Data)
    velocities: np.ndarray
    N: np.ndarray
    Fx: np.ndarray

    def __init__(self, vehicleName: str):

        # Loading in Vehicle Parameters
        df = pd.read_excel(f"Vehicles/{vehicleName}/parameters.xlsx")
        df["Symbol"] = df["Symbol"].str.strip()  # cleaning up excel values
        df["Value"] = df["Value"].apply(lambda x: str(x).strip() if isinstance(x, str) else x)  # cleaning up excel values
        dictParameters = dict(zip(df["Symbol"], df["Value"]))

        for key, value in dictParameters.items():
            setattr(self, key, value)
            print(f"{key} -> {value}")


        # Calculating Vehicle Parameters
        if self.drive_type == "RWD":
            self.num_dw = 2
            self.f_drive = 1 - self.d_fm
            self.f_aero = 1 - self.d_fa

        elif self.drive_type == "FWD":
            self.num_dw = 2
            self.f_drive = self.d_fm
            self.f_aero = self.d_fa

        else:
            self.num_dw = 4
            self.f_drive = 1
            self.f_aero = 1


    # Submodels

    # Description: Calculates vehicles velocity range using torque curve, drivetrain ratios,
    #              tire dimension, and other parameters. Also generates power curve diagram.
    # Returns: IDK MAYBE List containing all possible velocities of the vehicle given a step size for meshing and
    #          a power curve diagram.
    def powertrain(self):

        motorCurveDF = pd.read_excel(f"Vehicles/{self.name}/motor_curve.xlsx")

        motorSpeed = motorCurveDF["RPM"].to_numpy()  # RPM
        motorTorque = motorCurveDF["Torque (Nm)"].to_numpy()  # Nm
        motorPower = motorTorque * motorSpeed * 2*math.pi/60  # Watts

        wheelSpeed = motorSpeed / self.fdr  # RPM
        vehicleSpeed = math.pi * self.tire_d / 60 * wheelSpeed  # m/s
        vehicleMinSpeed = min(vehicleSpeed)
        vehicleMaxSpeed = max(vehicleSpeed)
        self.velocities = np.linspace(vehicleMinSpeed, vehicleMaxSpeed, int((vehicleMaxSpeed - vehicleMinSpeed) / dv) + 1)

        fig, ax1 = plt.subplots()

        # First Y-axis (left) — Torque
        ax1.plot(motorSpeed, motorTorque, color='blue', label='Torque (Nm)')
        ax1.set_xlabel('RPM')
        ax1.set_ylabel('Torque (Nm)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Second Y-axis (right) — Power
        ax2 = ax1.twinx()
        ax2.plot(motorSpeed, motorPower, color='orange', label='Power (W)')
        ax2.set_ylabel('Power (W)', color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')

        # Title & grid
        plt.title("Motor Curves")
        ax1.grid(True)

        plt.show()


    # Description: Calculates the normal and aero loads acting on the vehicle at differnt speeds.
    #              Track inclination and banking is not considered in this model.
    # Returns: idk yet bruh...
    def external_forces(self):

        # Z - Axis
        Fz_weight = self.m * -9.81  # weight of vehicle
        Fz_aero = 0.5 * self.rho * self.A * self.Cl * self.velocities ** 2  # force of downforce (or lift)
        Fz_frontAxle = Fz_weight * self.d_fm + Fz_aero * self.d_fa
        Fz_rearAxle = Fz_weight * (1 - self.d_fm) + Fz_aero * (1 - self.d_fa)
        N = abs(Fz_frontAxle + Fz_rearAxle)  # normal force

        # X - Axis
        Fx_aero = 0.5 * self.rho * self.A * self.Cd * self.velocities ** 2  # force of drag
        Fx_rr_frontAxle = 2 * self.Crr * abs(Fz_frontAxle)  # force of rolling resistance front axle
        Fx_rr_rearAxle =  2 * self.Crr * abs(Fz_rearAxle)  # force of rolling resistance rear axle
        Fx_rr = Fx_rr_frontAxle + Fx_rr_rearAxle  # force of rolling resistance on vehicle
        Fx = Fx_aero + Fx_rr  # forces acting on the x-axis


    # Description: Calculates the lateral and longitudinal grip limits of the vehicle at different speeds.
    # Returns: idk yet bruh...
    def tires(self):
        pass


    # Description: Driven channel for calculating driver braking forces.
    # Returns: idk yet bruh...
    def braking(self):
        pass


    # Description: Driven channel for calculating driver steering inputs.
    # Returns: idk yet bruh...
    def steering(self):
        pass


    # Description: Generates a GGV diagram representing the theoretical performance limits of the vehicle.
    # Returns: idk yet bruh...
    def ggv(self):
        pass


if __name__ == "__main__":
    model = Vehicle("F25")

    model.powertrain()
    model.external_forces()
