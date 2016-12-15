import sys
import threading
import termios
import tty
import select
import time
import RPi.GPIO as GPIO
from multiprocessing import Process, Value

from can2RNET import *


def induceJSMerror(canSocket):
    for i in range(3):
        cansend(canSocket,'0c000000#')


def RNET_JSMerror_exploit(canSocket):
    print('Waiting for JSM heartbeat')
    canwait(canSocket, '03C30F0F:1FFFFFFF')
    print('Waiting for joy frame')
    joy_id = getRNETjoystickFrameID(canSocket)
    print('Using joy frame: ' + joy_id)
    induceJSMerror(canSocket)
    print('3 x 0c000000# sent')
    return joy_id


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


def setSpeedRange(canSocket, speed_range):
    """Set speed_range from 0% - 100%."""
    if 0 <= speed_range and speed_range <= 100:
        cansend(canSocket,'0a040100#{:02x}'.format(speed_range))
    else:
        print('Invalid RNET SpeedRange: {}'.format(speed_range))


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


def initializeUltrasonicSensors(gpio_in, gpio_out):
    GPIO.setup(gpio_out, GPIO.OUT)
    GPIO.setup(gpio_in, GPIO.IN)
    GPIO.output(gpio_out, False)
    print("Waiting For Sensor To Settle")
    time.sleep(1)


def getDistance(echo, trig):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)
    while GPIO.input(echo) == 0:
        pulse_start = time.time()

    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return distance


def updateObstacles(obstaclePresent):
    bufferSize = 10
    numSensors = 3

    GPIO.setmode(GPIO.BCM)
    echoTrigPairs = [(17, 27), (5, 6), (13, 19)]
    for echo, trig in echoTrigPairs:
        initializeUltrasonicSensors(echo, trig)

    sensorValues = [[101] * bufferSize for i in range(numSensors)]
    while True:
        obstacles = False
        for i in range(numSensors):
            sensorValues[i].pop(0)
            sensorValues[i].append(getDistance(*echoTrigPairs[i]))
            average = sum(sensorValues[i]) / bufferSize
            if average < 80:
                obstacles = True
                break
        obstaclePresent.value = obstacles


def changeValuesByTime(x, y, obstaclePresent):
    while True:
        if obstaclePresent.value:
            y.value = 0
        else:
            y.value = 50
    # y.value = 155
    # time.sleep(3)


def setJoysticksFromApriltag(x, y, obstaclePresent):
    resolution = (1920, 1080)
    x_center = resolution[0] / 2
    x_scale = resolution[1] / 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Raspberry Pi IP address, AprilTags UDP port
    sock.bind(('172.20.10.5', 7709))
    while True:
        if obstaclePresent.value:
            x.value = 0
            y.value = 0
        else:
            data, addr = sock.recvfrom(1024)
            if len(data) == 24:
                print('No tags')
                x.value = 0
                y.value = 0
            elif len(data) == 112:
                d = struct.unpack('!8i20f', data)

                print('Corners: ({:4.0f},{:4.0f}); ({:4.0f},{:4.0f}); ({:4.0f},{:4.0f}); ({:4.0f},{:4.0f})'.format(*d[11:19]))
                width = max(max(abs(d[11] - d[13]), abs(d[13] - d[15])),
                            max(abs(d[15] - d[17]), abs(d[17] - d[11])))
                height = max(max(abs(d[12] - d[14]), abs(d[14] - d[16])),
                            max(abs(d[16] - d[18]), abs(d[18] - d[12])))
                size = max(width, height)
                print('X: {:4.0f}, Y: {:4.0f}, SIZE: {:4.0f}'.format(d[9], d[10], size))
                print('Calculated distance: {:3.2f} m; {:3.2f} ft'.format(
                    285 / size, 3.28084 * 285 / size))

                if size < 300:
                    print('going forward')
                    y.value = 50
                    x_val = d[9]
                    if x_val >= x_center:
                        x.value = int((x_val - x_center) * (80 / x_scale))
                    else:
                        x.value = 255 - int((x_center - x_val) * (80 / x_scale))
                elif size < 400:
                    print('stopping')
                    x.value = 0
                    y.value = 0
                else:
                    print('going backwards')
                    y.value = 255 - 50


if __name__ == "__main__":

    # canSocket = opencansocket(0)
    # setSpeedRange(canSocket, 0)
    # canwait(canSocket, '03C30F0F:1FFFFFFF')
    # joy_id = getRNETjoystickFrameID(canSocket)
    # induceJSMerror(canSocket)
    # mintime = .01
    # nexttime = time.time() + mintime

    # n_count = 220

    # count = 0
    # while count < n_count:
    #     cansend(canSocket, '{}#{:02x}{:02x}'.format(joy_id, 100, 0))
    #     time.sleep(.01)
    #     count += 1

    # count = 0
    # while count < n_count:
    #     cansend(canSocket, '{}#{:02x}{:02x}'.format(joy_id, 0, 0))
    #     time.sleep(.01)
    #     count += 1

    # count = 0
    # while count < 235:
    #     cansend(canSocket, '{}#{:02x}{:02x}'.format(joy_id, 155, 0))
    #     time.sleep(.01)
    #     count += 1
        # nexttime += mintime
        # t = time.time()
        # if t < nexttime:
        #     time.sleep(nexttime - t)
        # else:
        #     nexttime += mintime

    x = Value('i', 0)
    y = Value('i', 0)
    obstaclePresent = Value('b', False)

    # p1 = Process(target=changeValuesByTime, args=(x, y, obstaclePresent))
    p1 = Process(target=setJoysticksFromApriltag, args=(x, y, obstaclePresent))
    p2 = Process(target=sendJoystickValuesJSMerror, args=(x, y))
    p3 = Process(target=updateObstacles, args=(obstaclePresent,))

    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()
