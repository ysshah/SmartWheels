#!/usr/bin/env python3
from rplidar import RPLidar
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# Width of the wheelchair (or anything else) in meters
WIDTH = 1

def update_line(num, iterator, points, line):
    scan = np.array(next(iterator)).T

    # Number of data points
    N = scan.shape[1]

    # Angle in radians, rotated by 90 degrees
    angle = np.deg2rad((scan[1] + 90) % 360)

    # Get x and y coordinates in meters
    x = scan[2] / 1000 * np.cos(angle)
    y = scan[2] / 1000 * np.sin(angle)

    # ----------------------------------------------------------------------- #
    # Assign a cluster label to all points
    clusterNum = 0  # Initialize cluster number

    # Initialize array of cluster labels; one label for each point
    labels = np.zeros(N, dtype=int)

    for i in range(N):
        # For each point, compute the distance to the point behind it
        d = np.sqrt((x[i-1] - x[i])**2 + (y[i-1] - y[i])**2)

        if d > WIDTH:
            # If distance is greater than WIDTH, this point is in a new cluster
            clusterNum += 1

        labels[i] = clusterNum

    # If the last distance < WIDTH, the last cluster is same as first
    # (since we have wrapped all the way around 360 degrees)
    if d < WIDTH:
        labels[labels == clusterNum] = labels[0]
    # ----------------------------------------------------------------------- #

    # ----------------------------------------------------------------------- #
    # [Experimental] Draw a line from the center of the plot to an edge of
    # whichever cluster is directly in front (of the wheelchair)

    # Get the index of the data point whose angle is closest to pi/2 (which is
    # the "front" of the lidar)
    icenter = np.argmin(np.abs(angle - np.pi/2))

    if y[icenter] < 5:
        # If the point is less than 5 meters away, get the label of its cluster
        clusterBools = labels == labels[i]

        # Get the data point indices at which that cluster starts and ends, aka
        # the edges of that cluster. There should be two.
        changes = np.where(clusterBools[:-1] != clusterBools[1:])[0]
        if len(changes) == 2:
            # Draw a line from (0,0) to the right edge of the cluster. In the
            # future, this should probably compute whichever edge requires less
            # of a turn.
            ileft, iright = changes
            line.set_data([0, x[iright]], [0, y[iright]])
    else:
        line.set_data([0, 0], [0, y[icenter]])
    # ----------------------------------------------------------------------- #

    # Assign a different color to each cluster of points by cycling through the
    # list of colors.
    colors = np.array(['b'] * N)
    availableColors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    for i in range(clusterNum + 1):
        colors[labels == i] = availableColors[i % len(availableColors)]

    # Set new coordinates and colors of the points
    points.set_offsets(np.array([x, y]).T)
    points.set_facecolor(colors)


def run():
    """Create a live plot of the data points."""
    lidar = RPLidar('/dev/tty.SLAB_USBtoUART')
    time.sleep(0.1)

    fig, ax = plt.subplots(figsize=(8,8))
    ax.axis('scaled')
    ax.axis([10, -10, -10, 10])
    ax.grid(True)

    iterator = lidar.iter_scans()

    points = ax.scatter([0, 0], [0, 0], s=5, lw=0)
    line, = ax.plot([0, 1], [0, 1])

    ani = animation.FuncAnimation(fig, update_line,
        fargs=(iterator, points, line), interval=50)
    plt.show()

    lidar.stop()
    lidar.clear_input()
    lidar.stop_motor()
    lidar.disconnect()


if __name__ == '__main__':
    run()
