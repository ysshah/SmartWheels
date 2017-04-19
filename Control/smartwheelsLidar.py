import select
import argparse
import time
from multiprocessing import Process, Value

from rplidar import RPLidar

from can2RNET import *


def setSpeedRange(canSocket, speed_range):
    """Set speed_range from 0% - 100%."""
    if 0 <= speed_range and speed_range <= 100:
        cansend(canSocket,'0a040100#{:02x}'.format(speed_range))
    else:
        print('Invalid RNET SpeedRange: {}'.format(speed_range))


def getRNETjoystickFrameID(canSocket):
    """Get JoyFrame extendedID as text."""
    ready = select.select([canSocket], [], [], 1.0)
    if ready[0]:
        start = time.time()
        while (time.time() - start) < 1:
            cf, addr = canSocket.recvfrom(16)
            frameid = dissect_frame(cf).split('#')[0]
            if frameid[:3] == '020':
                return frameid
    raise TimeoutError('No RNET-Joystick frame seen')


def induceJSMerror(canSocket):
    for i in range(3):
        cansend(canSocket,'0c000000#')


def sendJoystickValuesJSMerror(x, y):
    canSocket = opencansocket(0)
    setSpeedRange(canSocket, 0)
    canwait(canSocket, '03C30F0F:1FFFFFFF')
    joystickID = getRNETjoystickFrameID(canSocket)
    induceJSMerror(canSocket)
    while True:
        cansend(canSocket, '{}#{:02x}{:02x}'.format(joystickID, x.value, y.value))
        time.sleep(.01)


def sendJoystickValues(x, y):
    canSocket = opencansocket(0)
    setSpeedRange(canSocket, 0)
    rnet_joystick_id = getRNETjoystickFrameID(canSocket)
    rnet_joystick_frame_raw = build_frame(rnet_joystick_id + '#0000')
    while True:
        cf, addr = canSocket.recvfrom(16)
        if cf == rnet_joystick_frame_raw:
            cansend(canSocket, '{}#{:02x}{:02x}'.format(
                rnet_joystick_id, x.value, y.value))


def updateObstacles(obstacleBooleans):
    lidar = RPLidar('/dev/ttyUSB0')
    time.sleep(0.1)

    try:
        # for new_scan, quality, angle, distance in lidar.iter_measurments():
        #     if angle < 0.5 or angle > 359.5:
        #         print(quality, distance)
        #         obstacleBooleans.value = distance < 800

        for scan in lidar.iter_scans():
            distances = [x[2]/10 for x in filter(
                lambda x: 170 < x[1] and x[1] < 190, scan)]
            N = len(distances)
            if N:
                mean = sum(distances) / N
                print(mean)
                obstacleBooleans.value = mean < 80
            else:
                obstacleBooleans.value = False
    except KeyboardInterrupt:
        print('Keyboard interrupt, stopping and disconnecting lidar.')
        lidar.stop()
        lidar.stop_motor()
        lidar.disconnect()


def setJoysticksFromApriltag(x, y, obstacleBooleans):
    resolution = (1920, 1080)
    x_center = resolution[0] / 2
    x_scale = resolution[1] / 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Raspberry Pi IP address, AprilTags UDP port
    sock.bind(('172.20.10.5', 7709))
    lastSeenTime = time.time()

    # 0 = left, 1 = right
    lastSeenDirection = 0
    while True:

        obstacle = obstacleBooleans.value
        if obstacle:
            print('Obstacles in front')
            obstacle = obstacleBooleans.value
            while obstacle:
                y.value = 0
                x.value = 0
                time.sleep(0.5)
                obstacle = obstacleBooleans.value
            print('Leaving loop')

        else:
            x.value = 0
            y.value = 32
            # data, addr = sock.recvfrom(1024)
            # if len(data) == 24:
            #     y.value = 0
            #     if time.time() - lastSeenTime > 3:
            #         if lastSeenDirection == 1:
            #             x.value = 50
            #         else:
            #             x.value = 255 - 50
            #     else:
            #         x.value = 0
            # elif len(data) == 112:
            #     lastSeenTime = time.time()

            #     d = struct.unpack('!8i20f', data)

            #     width = max(max(abs(d[11] - d[13]), abs(d[13] - d[15])),
            #                 max(abs(d[15] - d[17]), abs(d[17] - d[11])))
            #     height = max(max(abs(d[12] - d[14]), abs(d[14] - d[16])),
            #                 max(abs(d[16] - d[18]), abs(d[18] - d[12])))
            #     size = max(width, height)
            #     distanceToAprilTag = 285 / size  # Roughly meters

            #     if distanceToAprilTag > 1.0:
            #         y.value = 50
            #         x_val = d[9]
            #         if x_val >= x_center:
            #             x.value = int((x_val - x_center) * (80 / x_scale))
            #             lastSeenDirection = 1
            #         else:
            #             x.value = 255 - int((x_center - x_val) * (80 / x_scale))
            #             lastSeenDirection = 0
            #     elif distanceToAprilTag > 0.85:
            #         x.value = 0
            #         y.value = 0
            #     else:
            #         y.value = 255 - 50


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--follow', action='store_true',
        help='Follow AprilTag only, no obstacle avoidance')
    args = parser.parse_args()

    x = Value('i', 0)
    y = Value('i', 0)
    obstacleBooleans = Value('b', False)
    # obstacleBooleans = (
    #     Value('b', False), Value('b', False), Value('b', False)
    # )

    if args.follow:
        print('Follow only mode activated - obstacle avoidance OFF.')
    else:
        obstacleProcess = Process(target=updateObstacles,
            args=(obstacleBooleans,))
        obstacleProcess.start()
        time.sleep(3)
        print('Obstacle avoidance ON.')

    sendJoystickValuesProcess = Process(target=sendJoystickValuesJSMerror,
        args=(x, y))
    sendJoystickValuesProcess.start()

    setJoystickProcess = Process(target=setJoysticksFromApriltag,
        args=(x, y, obstacleBooleans))
    setJoystickProcess.start()

    sendJoystickValuesProcess.join()
    setJoystickProcess.join()
