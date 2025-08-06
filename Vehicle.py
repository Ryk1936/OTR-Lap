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
    fdr: float  # final drive ratio
    eta: float  # drivetrain efficiency
    tire_d: float  # tire diameter [in]
    tire_w: float  # tire width [in]
    R_e: float  # tire rolling radius / effective radius
    mu_x: float  # tire coefficent of friction longitudinal
    mu_y: float  # tire coefficent of friction lateral (UNUSED CURRENTLY)
    Crr: float  # rollling resistance coefficent
    B: float  # magic formula stiffness factor
    C: float  # magic formula shape factor
    D: float  # magic formula peak value (MAY NOT NEED THIS VALUE)
    E: float  # magic formula curvature factor

    # Calculated Vehicle Parameters
    num_dw: int  # number of driven wheels
    f_drive: float
    f_aero: float

    # Forces and Velocity (GGV Plot Data)
    velocities: np.ndarray
    N: np.ndarray  # normal force -> Fz_aero + Fz_weight
    N_dw: np.ndarray  # normal force on driven wheels
    Fx_motor: np.ndarray  # motor tractive force
    Fx_aero: np.ndarray  # aerodynamic drag
    Fx_rr: np.ndarray # rolling resistance
    Fz_weight: float  # vehicle weight
    Fz_aero: np.ndarray  # aerodynamic downforce
    Fx_tires_accel: np.ndarray  # longitudinal forces tires can provide when accelerating (only driven wheels)
    Fx_tires_deccel: np.ndarray  # longitudinal forces tires can provide when deccelerating (all wheels)
    Fy_tires: np.ndarray  # lateral forces tires can provide (all wheels)


    def __init__(self, vehicleName: str):

        # Loading in Vehicle Parameters
        df = pd.read_excel(f"Vehicles/{vehicleName}/parameters.xlsx")
        df["Symbol"] = df["Symbol"].str.strip()  # cleaning up excel values
        df["Value"] = df["Value"].apply(lambda x: str(x).strip() if isinstance(x, str) else x)  # cleaning up excel values
        dictParameters = dict(zip(df["Symbol"], df["Value"]))

        for key, value in dictParameters.items():
            setattr(self, key, value)

        # PARAMETER OVERRIDE (for debugging and GGV plot understanding)
        # self.Cl = -10
        self.fdr = 3.6
        self.eta = 1
        self.R_e = 9

        # Unit Conversions
        self.tire_d = self.tire_d / 39.37  # in to m
        self.tire_w = self.tire_w / 39.37  # in to m
        self.R_e = self.R_e / 39.37  # in to m

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
    # Raises:
    def powertrain(self):

        # TODO: Fix plotting code. Make it more understandable.

        # Loading in motor curve data
        motorCurveDF = pd.read_excel(f"Vehicles/{self.name}/motor_curve.xlsx")

        # Vehicle max/min speed and velocity meshing
        motorSpeed = motorCurveDF["RPM"].to_numpy()  # RPM
        motorTorque = motorCurveDF["Torque (Nm)"].to_numpy() # Nm
        motorPower = motorTorque * motorSpeed * 2*math.pi/60  # Watts

        wheelSpeed = motorSpeed / self.fdr  # in RPM   #  gear ratios do not cause speed losses only torque and power loss
        vehicleSpeed = math.pi * self.R_e * 2 / 60 * wheelSpeed  # m/s
        vehicleMinSpeed = min(vehicleSpeed)
        vehicleMaxSpeed = max(vehicleSpeed)
        self.velocities = np.linspace(vehicleMinSpeed, vehicleMaxSpeed, int((vehicleMaxSpeed - vehicleMinSpeed) / dv) + 1)
        print(f"Max Speed: {vehicleMaxSpeed * 3.6}")

        # Motor tractive forces
        wheelSpeed_2 = self.velocities * 60 / math.pi * self.R_e * 2
        motorSpeed_2 = wheelSpeed_2 * self.fdr  # in RPM
        motorTorque_2 = np.interp(motorSpeed_2, motorSpeed, motorTorque)
        self.Fx_motor = motorTorque_2 * self.fdr * self.eta / self.R_e  # drivetrain efficency accounted for

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
    # Raises:
    def external_forces(self):

        # TODO: Add induced drag effects of steered front tires.

        # Z - Axis
        self.Fz_weight = self.m * -9.81  # weight of vehicle
        self.Fz_aero = 0.5 * self.rho * self.A * self.Cl * self.velocities ** 2  # force of downforce (or lift)
        Fz_frontAxle = self.Fz_weight * self.d_fm + self.Fz_aero * self.d_fa
        Fz_rearAxle = self.Fz_weight * (1 - self.d_fm) + self.Fz_aero * (1 - self.d_fa)
        self.N = abs(Fz_frontAxle + Fz_rearAxle)  # total normal force
        self.N_dw = (self.f_drive * self.Fz_weight + self.f_aero * self.Fz_aero) / self.num_dw

        # X - Axis
        self.Fx_aero = 0.5 * self.rho * self.A * self.Cd * self.velocities ** 2  # force of drag
        Fx_rr_frontAxle = 2 * self.Crr * abs(Fz_frontAxle)  # force of rolling resistance front axle
        Fx_rr_rearAxle =  2 * self.Crr * abs(Fz_rearAxle)  # force of rolling resistance rear axle
        self.Fx_rr = Fx_rr_frontAxle + Fx_rr_rearAxle  # force of rolling resistance on vehicle (CHECK SIGN)
        print(self.Fx_aero)


    # Description: Calculates the lateral and longitudinal grip limits of the vehicle at different speeds.
    # Raises:
    def tires(self):

        # TODO: Add normal load distribution consisderation for front and rear wheels.
        # TODO: Include normal load sensitivity consisderations

        slipAngle_deg = np.linspace(-15, 15, 500)  # sweep slip angle from -15 deg to 15 deg.
        slipAngle_rad = np.radians(slipAngle_deg)
        slipRatio = np.linspace(-0.3, 0.3, 500)  # sweep slip ratio from -30% to 30%.
        N_values = np.linspace(min(self.N), max(self.N), len(self.velocities)) / 4  # assuming equal weight distribution on all wheels

        def magic_formula(x, B, C, D, E):
            return D * np.sin(C * np.arctan(B * x - E * (B * x - np.arctan(B * x))))

        # single tire Fx values
        Fx_tire = np.zeros(len(N_values))
        for i in range(len(N_values)):
            D = self.mu_y * N_values[i]  # no normal load sensitivity considered***
            Fx_tire[i] = np.max(magic_formula(slipRatio, self.B, self.C, D, self.E))

        # single tire Fy values
        Fy_tire = np.zeros(len(N_values))
        for i in range(len(N_values)):
            D = self.mu_y * N_values[i]
            Fy_tire[i] = np.max(magic_formula(slipAngle_rad, self.B, self.C, D, self.E))

        self.Fx_tires_accel = Fx_tire * self.num_dw
        self.Fx_tires_deccel = Fx_tire * 4
        self.Fy_tires = Fy_tire * 4


    # Description: Driven channel for calculating driver braking forces.
    # Raises:
    def braking(self):
        # TODO: Calculate brake pressure.
        pass


    # Description: Driven channel for calculating driver steering inputs.
    # Raises:
    def steering(self):
        # TODO: Calculate steering angle.
        pass


    # Description: Generates a GGV diagram representing the theoretical performance limits of the vehicle.
    # Raises:
    def ggv(self):

        # TODO: Fix Bugs. Not displaying a physically possible GGV diagram.

        # n = 50
        #
        # # Acceleration from aero
        # ax_drag = self.Fx_aero / self.m  # drag acceleration
        #
        # # Acceleration from motor
        # ax_motor = self.Fx_motor / self.m  # max positive longitudinal tractive force from motor
        #
        # # Accleration from tires
        # ax_tire_max_accel = self.Fx_tires_accel / self.m  # max positive longitudinal force provided by driven wheels
        # ax_tire_max_decel = self.Fx_tires_deccel / self.m  # max negative longitudinal force provided by tires
        # ay_max = self.Fy_tires / self.m  # max lateral force provided by tires
        #
        # ay = ay_max * np.cos(np.linspace(0, np.pi, n))
        # ax_tire_accel = ax_tire_max_accel * np.sqrt(1 - (ay / ay_max)**2)
        # ax_accel = min(ax_tire_accel, ax_motor) + ax_drag
        # ax_deccel = ax_tire_max_decel * np.sqrt(1 - (ay / ay_max)**2) + ax_drag

        n = 20

        ax_surf = []  # will be shape (2*n, len(velocities))
        ay_surf = []  # same shape
        v_surf = []  # same shape

        for i in range(len(self.velocities)):
            ay_max_i = self.Fy_tires[i] / self.m
            ax_motor_i = self.Fx_motor[i] / self.m
            ax_tire_accel_i = self.Fx_tires_accel[i] / self.m
            ax_tire_decel_i = self.Fx_tires_deccel[i] / self.m
            ax_drag_i = self.Fx_aero[i] / self.m
            print(ax_drag_i)

            ay_angles = np.linspace(0, np.pi, n)
            ay = ay_max_i * np.cos(ay_angles)

            ax_accel = np.minimum(ax_tire_accel_i * np.sqrt(1 - (ay / ay_max_i) ** 2), ax_motor_i) + ax_drag_i
            ax_decel = -ax_tire_decel_i * np.sqrt(1 - (ay / ay_max_i) ** 2) + ax_drag_i

            ax_col = np.concatenate([ax_decel[::-1], [np.nan], ax_accel])
            ay_col = np.concatenate([-ay[::-1], [np.nan], ay])  # mirror lateral acceleration

            ax_surf.append(ax_col)
            ay_surf.append(ay_col)
            v_surf.append(np.full_like(ax_col, self.velocities[i]))

        # Convert to 2D numpy arrays of shape (len(velocities), 2*n)
        ax_surf = np.array(ax_surf).T  # shape: (2*n, len(velocities))
        ay_surf = np.array(ay_surf).T
        v_surf = np.array(v_surf).T

        import matplotlib as mpl
        mpl.rcParams['toolbar'] = 'none'  # remove toolbar

        # Create figure
        fig = plt.figure(figsize=(12, 10))

        # 1. Isometric view
        ax1 = fig.add_subplot(221, projection='3d')
        ax1.plot_surface(ax_surf, ay_surf, v_surf, cmap='viridis', edgecolor='none')
        ax1.set_xlabel('Longitudinal Acceleration (m/s²)')
        ax1.set_ylabel('Lateral Acceleration (m/s²)')
        ax1.set_zlabel('Velocity (m/s)')
        ax1.view_init(elev=25, azim=-45)
        ax1.set_title("Isometric View")

        # 2. Top view
        ax2 = fig.add_subplot(222, projection='3d')
        ax2.set_proj_type('ortho')
        ax2.plot_surface(ax_surf, ay_surf, v_surf, cmap='viridis', edgecolor='none')
        ax2.view_init(elev=90, azim=-90)
        ax2.set_xlabel('Longitudinal Acceleration (m/s²)')
        ax2.set_ylabel('Lateral Acceleration (m/s²)')
        ax2.set_zticklabels([])  # remove stacked labels
        ax2.set_title("Top View")

        # 3. Side view
        ax3 = fig.add_subplot(223, projection='3d')
        ax3.set_proj_type('ortho')
        ax3.plot_surface(ax_surf, ay_surf, v_surf, cmap='viridis', edgecolor='none')
        ax3.view_init(elev=0, azim=0)
        ax3.set_ylabel('Lateral Acceleration (m/s²)')
        ax3.set_zlabel('Velocity (m/s)')
        ax3.set_xticklabels([])  # remove stacked labels
        ax3.set_title("Side View")

        # 4. Back view
        ax4 = fig.add_subplot(224, projection='3d')
        ax4.set_proj_type('ortho')
        ax4.plot_surface(ax_surf, ay_surf, v_surf, cmap='viridis', edgecolor='none')
        ax4.view_init(elev=0, azim=90)
        ax4.set_xlabel('Longitudinal Acceleration (m/s²)')
        ax4.set_zlabel('Velocity (m/s)')
        ax4.set_yticklabels([])  # remove stacked labels
        ax4.set_title("Back View")

        plt.ioff()
        plt.show()


if __name__ == "__main__":
    model = Vehicle("F24_Continuous_Torque")

    model.powertrain()
    model.external_forces()
    model.tires()
    model.ggv()
