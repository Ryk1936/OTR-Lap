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
    name: str
    mass: float
    d_fm: float  # front weight distribution percentage
    Cl: float
    Cd: float
    d_fa: float  # front aero distribution percentage
    frontalArea: float
    airDensity: float
    driveType: str
    finalDriveRatio: float
    tireDiameter: float
    tireWidth: float
    Cr: float  # single tire rolling resistance coefficent

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
        parametersDF = pd.read_excel(f"Vehicles/{vehicleName}/parameters.xlsx")

        # gotta find a better way to do this bruh. not very scalable at the moment.
        self.name = parametersDF["Value"][0]
        self.mass = parametersDF["Value"][1]
        self.d_fm = parametersDF["Value"][2]
        self.Cl = parametersDF["Value"][3]
        self.Cd = parametersDF["Value"][4]
        self.d_fa = parametersDF["Value"][5]
        self.frontalArea = parametersDF["Value"][6]
        self.airDensity = parametersDF["Value"][7]
        self.driveType = parametersDF["Value"][8]
        self.finalDriveRatio = parametersDF["Value"][9]
        self.tireDiameter = parametersDF["Value"][10] / 39.37  # conversion from inch to metres
        self.tireWidth = parametersDF["Value"][11] / 39.37  # conversion from inch to metres
        self.Cr = parametersDF["Value"][12]

        # Calculating Vehicle Parameters
        if self.driveType == "RWD":
            self.num_dw = 2
            self.f_drive = 1 - self.d_fm
            self.f_aero = 1 - self.d_fa

        elif self.driveType == "FWD":
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

        wheelSpeed = motorSpeed / self.finalDriveRatio  # RPM
        vehicleSpeed = math.pi * self.tireDiameter / 60 * wheelSpeed  # m/s
        vehicleMinSpeed = min(vehicleSpeed)
        vehicleMaxSpeed = max(vehicleSpeed)
        self.velocities = np.linspace(vehicleMinSpeed, vehicleMaxSpeed, int((vehicleMaxSpeed - vehicleMinSpeed) / dv) + 1)

        # plt.figure()
        # plt.plot(motorSpeed, motorTorque)
        # plt.xlabel("RPM")
        # plt.ylabel("Torque (Nm)")
        # plt.title("Motor Torque Curve")
        # plt.grid(True)
        #
        # plt.figure()
        # plt.plot(motorSpeed, motorPower, color='orange')
        # plt.xlabel("RPM")
        # plt.ylabel("Power (W)")
        # plt.title("Motor Power Curve")
        # plt.grid(True)
        #
        # plt.show()


    # Description: Calculates the normal and aero loads acting on the vehicle at differnt speeds.
    #              Track inclination and banking is not considered in this model.
    # Returns: idk yet bruh...
    def external_forces(self):

        # Z - Axis
        Fz_weight = self.mass * -9.81  # weight of vehicle
        Fz_aero = 0.5 * self.airDensity * self.frontalArea * self.Cl * self.velocities ** 2  # force of downforce (or lift)
        Fz_frontAxle = Fz_weight * self.d_fm + Fz_aero * self.d_fa
        Fz_rearAxle = Fz_weight * (1 - self.d_fm) + Fz_aero * (1 - self.d_fa)
        N = abs(Fz_frontAxle + Fz_rearAxle)  # normal force

        # X - Axis
        Fx_aero = 0.5 * self.airDensity * self.frontalArea * self.Cd * self.velocities ** 2  # force of drag
        Fx_rr_frontAxle = 2 * self.Cr * abs(Fz_frontAxle)  # force of rolling resistance front axle
        Fx_rr_rearAxle =  2 * self.Cr * abs(Fz_rearAxle)  # force of rolling resistance rear axle
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
