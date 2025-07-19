# July 9th 2025
# Author: Ryan Koo - Ontario Tech Racing
# Description: Displays map of a given racing track with velocity and acceleration
#              shown as a colour gradient.

# General Definitions
# (x1, y1) - Current map point used to compute the next point.
# (x2, y2) - The next point map point to be calculated.

import csv
import math
import numpy as np
import matplotlib.pyplot as plt

def generateGradientMaps(trackFile: str, stepSize: float):
    # Variables
    listX = [0]
    listY = [0]
    theta = 0  # in radians

    # Loading in Track Data and Map Generation
    with open(trackFile, mode='r') as file:
        data = csv.reader(file)

        for segment in data:
            segmentLength = float(segment[0])
            segmentRadius = float(segment[1])

            x1 = listX[len(listX) - 1]
            y1 = listY[len(listY) - 1]

            # straight segment cases
            if segmentRadius == 0:
                for _ in range(int(segmentLength / stepSize)):
                    x2 = x1 + stepSize * math.cos(theta)
                    y2 = y1 + stepSize * math.sin(theta)

                    x1 = x2
                    y1 = y2

                    listX.append(x2)
                    listY.append(y2)

                remainder = segmentLength % stepSize
                if remainder != 0:
                    x2 = x1 + remainder * math.cos(theta)
                    y2 = y1 + remainder * math.sin(theta)

                    x1 = x2
                    y1 = y2

                    listX.append(x1)
                    listY.append(y1)


            # left turning segment case
            elif segmentRadius > 0:
                for _ in range(int(segmentLength / stepSize)):
                    xc = x1 + segmentRadius * math.cos(theta + math.pi / 2)
                    yc = y1 + segmentRadius * math.sin(theta + math.pi / 2)

                    phi = stepSize / segmentRadius

                    # original point matrix
                    p1 = np.array([[x1],
                                   [y1]])

                    # rotation matrix
                    t1 = np.array([[math.cos(phi), -1 * math.sin(phi)],
                                   [math.sin(phi), math.cos(phi)]])

                    # translation matrix
                    t2 = np.array([[xc],
                                   [yc]])

                    # solving next point
                    p2 = t1 @ (p1 - t2) + t2

                    x1 = p2[0, 0]
                    y1 = p2[1, 0]

                    listX.append(x1)
                    listY.append(y1)

                    theta += phi

                remainder = segmentLength % stepSize
                if remainder != 0:
                    xc = x1 + segmentRadius * math.cos(theta + math.pi / 2)
                    yc = y1 + segmentRadius * math.sin(theta + math.pi / 2)

                    phi = remainder / segmentRadius

                    # original point matrix
                    p1 = np.array([[x1],
                                   [y1]])

                    # rotation matrix
                    t1 = np.array([[math.cos(phi), -1 * math.sin(phi)],
                                   [math.sin(phi), math.cos(phi)]])

                    # translation matrix
                    t2 = np.array([[xc],
                                   [yc]])

                    # solving next point
                    p2 = t1 @ (p1 - t2) + t2

                    x1 = p2[0, 0]
                    y1 = p2[1, 0]

                    listX.append(x1)
                    listY.append(y1)

                    theta += phi

            # right turning segment case
            else:
                for _ in range(int(segmentLength / stepSize)):
                    xc = x1 + segmentRadius * math.cos(theta - math.pi / 2)
                    yc = y1 + segmentRadius * math.sin(theta - math.pi / 2)

                    phi = -1 * stepSize / segmentRadius

                    # original point matrix
                    p1 = np.array([[x1],
                                   [y1]])

                    # rotation matrix
                    t1 = np.array([[math.cos(phi), -1 * math.sin(phi)],
                                   [math.sin(phi), math.cos(phi)]])

                    # translation matrix
                    t2 = np.array([[xc],
                                   [yc]])

                    # solving next point
                    p2 = t1 @ (p1 - t2) + t2

                    x1 = p2[0, 0]
                    y1 = p2[1, 0]

                    listX.append(x1)
                    listY.append(y1)

                    theta -= phi

                remainder = segmentLength % stepSize
                if remainder != 0:
                    xc = x1 + segmentRadius * math.cos(theta - math.pi / 2)
                    yc = y1 + segmentRadius * math.sin(theta - math.pi / 2)

                    phi = -1 * remainder / segmentRadius

                    # original point matrix
                    p1 = np.array([[x1],
                                   [y1]])

                    # rotation matrix
                    t1 = np.array([[math.cos(phi), -1 * math.sin(phi)],
                                   [math.sin(phi), math.cos(phi)]])

                    # translation matrix
                    t2 = np.array([[xc],
                                   [yc]])

                    # solving next point
                    p2 = t1 @ (p1 - t2) + t2

                    x1 = p2[0, 0]
                    y1 = p2[1, 0]

                    listX.append(x1)
                    listY.append(y1)

                    theta -= phi


    # PLOTTING WAS GPT'D....
    from matplotlib.collections import LineCollection

    # === Load Velocities from CSV ===
    velocities = []
    with open("track velocities.csv", mode='r') as file:
        data = csv.reader(file)
        for row in data:
            try:
                velocities.append(float(row[1]))
            except:
                pass  # Skip bad rows if any

    # === Sync data lengths ===
    minLen = min(len(velocities), len(listX) - 1)
    velocities = velocities[:minLen]
    plotX = [(listX[i] + listX[i + 1]) / 2 for i in range(minLen)]
    plotY = [(listY[i] + listY[i + 1]) / 2 for i in range(minLen)]

    # === Compute Acceleration Profile (central difference) ===
    stepSize = 0.1  # adjust to your actual step size
    accelerations = []
    for i in range(minLen):
        if i == 0:
            acc = (velocities[1] - velocities[0]) / stepSize
        elif i == minLen - 1:
            acc = (velocities[-1] - velocities[-2]) / stepSize
        else:
            acc = (velocities[i + 1] - velocities[i - 1]) / (2 * stepSize)
        accelerations.append(float(acc))


    # === Function to create LineCollection for gradient line ===
    def create_line_collection(x, y, values, cmap_name='jet'):
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap_name, norm=plt.Normalize(min(values), max(values)))
        lc.set_array(np.array(values))
        lc.set_linewidth(3)
        return lc


    # === Create figure with 2 subplots side-by-side ===
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 6))

    # Velocity Gradient Plot
    lc_vel = create_line_collection(plotX, plotY, velocities, 'jet')
    ax1.add_collection(lc_vel)
    ax1.autoscale()
    ax1.set_aspect('equal')
    ax1.set_title('Track Velocity Gradient')
    ax1.set_xlabel('x (m)')
    ax1.set_ylabel('y (m)')
    ax1.grid(True)
    cbar1 = fig.colorbar(lc_vel, ax=ax1)
    cbar1.set_label('Velocity (m/s)')

    # Acceleration Gradient Plot
    lc_acc = create_line_collection(plotX, plotY, accelerations, 'jet')
    ax2.add_collection(lc_acc)
    ax2.autoscale()
    ax2.set_aspect('equal')
    ax2.set_title('Track Acceleration Gradient')
    ax2.set_xlabel('x (m)')
    ax2.set_ylabel('y (m)')
    ax2.grid(True)
    cbar2 = fig.colorbar(lc_acc, ax=ax2)
    cbar2.set_label('Acceleration (m/s²)')

    plt.tight_layout()
    plt.show()
