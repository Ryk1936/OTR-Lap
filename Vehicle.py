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



class Vehicle:
    name: str
    mass: float
    dfm: float  # front weight distribution percentage
    Cl: float
    Cd: float
    dam: float  # front aero distribution percentage
    frontalArea: float
    airDensity: float
    driveType: float
    finalDriveRatio: float
    tireDiameter: float
    tireWidth: float

    velocities: float

    def __init__(self, vehicleName: str):
        parametersDF = pd.read_excel(f"Vehicles/{vehicleName}/parameters.xlsx")

        # gotta find a better way to do this bruh. not very scalable at the moment.
        self.name = parametersDF["Value"][0]
        self.mass = parametersDF["Value"][1]
        self.dfm = parametersDF["Value"][2]
        self.Cl = parametersDF["Value"][3]
        self.Cd = parametersDF["Value"][4]
        self.dam = parametersDF["Value"][5]
        self.frontalArea = parametersDF["Value"][6]
        self.airDensity = parametersDF["Value"][7]
        self.driveType = parametersDF["Value"][8]
        self.finalDriveRatio = parametersDF["Value"][9]
        self.tireDiameter = parametersDF["Value"][10] / 39.37  # conversion from inch to metres
        self.tireWidth = parametersDF["Value"][11] / 39.37  # conversion from inch to metres

        powertrain()


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
        self.velocities = vehicleSpeed * 3.6  # km/h

        plt.figure()
        plt.plot(motorSpeed, motorTorque)
        plt.xlabel("RPM")
        plt.ylabel("Torque (Nm)")
        plt.title("Motor Torque Curve")
        plt.grid(True)

        plt.figure()
        plt.plot(motorSpeed, motorPower, color='orange')
        plt.xlabel("RPM")
        plt.ylabel("Power (W)")
        plt.title("Motor Power Curve")
        plt.grid(True)

        plt.show()


    # Description: Calculates the normal and aero loads acting on the vehicle at differnt speeds.
    # Returns: idk yet bruh...
    def external_forces(self, velocity: float):
        pass


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
