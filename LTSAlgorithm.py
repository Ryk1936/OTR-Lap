# July 4th 2025
# Author: Ryan Koo - Ontario Tech Racing
# Description: Simple lap time simulator algorithm using a given track and gg-circle radius.
#              No vehicle model is used for simulated lap times. More of just a proof of concept.

# General Definitions:
# Segment - A turn or a straight on the track.
# Straight - A segment of the track with no curvature. Represented by some length and a radius of 0.
# Turn - A segment of the track that is curved. Represented by some length and some value of radius.
# Step - A point on a segment where the velocity is calculated.


import csv
import math
import matplotlib.pyplot as plt
import GradientMaps


# Simulation Preferences
TRACK_FILE_NAME = "Tracks/Autocross_Michigan.csv"
stepSize = .1  # mesh step size in meters. increase for better accuracy but longer runtime.
ggCircleRadius = 2  # in g's
tempNumStepsToGen = 10


# Objects
class Turn:
    length = None
    radius = None
    velocity = None  # constant velocity throughout the segment
    trackIndexStart = None  # index location of the segment's first step in the track mesh
    trackIndexEnd = None  # index location of the segment's last step in the track mesh

    def __init__(self, length: float, radius: float):
        self.length = length
        self.radius = radius

        self.velocity = math.sqrt(accel_y * radius)

    def get_velocity(self):
        return self.velocity

    def get_track_index_start(self):
        return self.trackIndexStart

    def get_track_index_end(self):
        return self.trackIndexEnd

    def set_track_index_start(self, index: int):
        self.trackIndexStart = index
        self.trackIndexEnd = index + int(self.length / stepSize)

        if self.length % stepSize != 0: self.trackIndexEnd += 1

    def __repr__(self):
        return f"Max Velocity: {round(self.velocity, 2)} m/s"


# Variables
listStraights = []
listTurns = []
trackMesh = {}  # {<track index> : {"delX" : <distance to next>, "velocity" : [possible velocity solutions]}}

# Math Variables
accel_x = ggCircleRadius * 9.81  # in m/s^2
accel_y = ggCircleRadius * 9.81  # in m/s^2


# LAP TIME SIMULATION ALGORITHM =================================================================================
# Loading in Track Data
with open(TRACK_FILE_NAME, mode='r') as file:
    data = csv.reader(file)

    for segment in data:
        segmentLength = float(segment[0])
        segmentRadius = abs(float(segment[1]))  # direction of turn is not relevant in velocity calculations

        # Loading Turns and Solving Apex Velocities
        if segmentRadius != 0:
            turnObject = Turn(segmentLength, segmentRadius)
            velocity = [turnObject.get_velocity()]
            turnObject.set_track_index_start(len(trackMesh))
            listTurns.append(turnObject)  # store turn data
        else:
            velocity = []  # velocity steps on straights solved later

        # Track Mesh and Track Velocity Generation
        for i in range(int(segmentLength / stepSize) + (1 if segmentRadius != 0 else -1)):
            # track mesh generation

            trackMesh[len(trackMesh)] = {"delX": stepSize, "velocities": velocity.copy()}

        remainder = segmentLength % stepSize
        if remainder != 0:
            trackMesh[len(trackMesh)] = {"delX": remainder, "velocities": velocity.copy()}

# Apex Sorting by Velocity
listTurnsApexSorted = sorted(listTurns, key=lambda turn: turn.velocity)  # sorts apex velocities least to greatest

# Calculating Acceleration Velocity Steps (From Standing Start - 0 m/s)
trackMesh[0]["velocities"].append(0.0)
nextStepIndex = 1
previousStepVelocity = 0

velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

while not trackMesh[nextStepIndex]["velocities"] or velocity < min(trackMesh[nextStepIndex]["velocities"]):
    trackMesh[nextStepIndex]["velocities"].append(velocity)

    nextStepIndex += 1

    if nextStepIndex in trackMesh:
        previousStepVelocity = velocity
        velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

    else:
        break  # reached end of track

# Calculating Acceleration Velocity Steps (Exiting a Turn)
for turnSegment in listTurnsApexSorted:

    nextStepIndex = turnSegment.get_track_index_end() + 1
    if nextStepIndex not in trackMesh: continue

    previousStepVelocity = turnSegment.get_velocity()

    velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

    while not trackMesh[nextStepIndex]["velocities"] or velocity < min(trackMesh[nextStepIndex]["velocities"]):
        trackMesh[nextStepIndex]["velocities"].append(velocity)

        nextStepIndex += 1

        if nextStepIndex in trackMesh:
            previousStepVelocity = velocity
            velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

        else:
            break  # reached end of track

# Calculating Deceleration Velocity Steps (Entering a Turn)
for turnSegment in listTurnsApexSorted:

    nextStepIndex = turnSegment.get_track_index_start() - 1
    if nextStepIndex not in trackMesh: continue

    previousStepVelocity = turnSegment.get_velocity()

    velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

    while not trackMesh[nextStepIndex]["velocities"] or velocity < min(trackMesh[nextStepIndex]["velocities"]):
        trackMesh[nextStepIndex]["velocities"].append(velocity)

        nextStepIndex -= 1

        if nextStepIndex in trackMesh:
            previousStepVelocity = velocity
            velocity = math.sqrt(previousStepVelocity ** 2 + 2 * accel_x * trackMesh[nextStepIndex]["delX"])

        else:
            break  # reached beginning of track

# Calculating Total Lap Time
totalTime = 0

for step in trackMesh.values():
    if min(step["velocities"]) == 0: continue
    totalTime += step["delX"] / min(step["velocities"])

print(f"Lap Time: {round(totalTime, 2)} s")

# PLOTTING WAS GPT'D....
cumulative_distance = 0
x_points = []
y_points = []

for i in range(len(trackMesh)):
    step = trackMesh[i]

    x_points.append(cumulative_distance)
    y_points.append(min(step["velocities"]))

    cumulative_distance += step['delX']

# output data for GradientMaps.py
outFile = "track velocities.csv"

with open(outFile, mode='w', newline='') as file:
    writer = csv.writer(file)

    for i in range(len(x_points)):
        writer.writerow([x_points[i], y_points[i]])


# Plotting
plt.figure(figsize=(20, 5))
plt.scatter(x_points, y_points, color='blue', marker='o', s=5)
plt.title('Velocity vs. Distance')
plt.xlabel('Distance (m)')
plt.ylabel('Velocity (m/s)')
plt.grid(True)
plt.show(block=False)

# Velocity and Acceleration Gradient Maps
GradientMaps.generateGradientMaps(TRACK_FILE_NAME, stepSize)


