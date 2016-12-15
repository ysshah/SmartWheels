import select
import time
import RPi.GPIO as GPIO
from multiprocessing import Process, Value

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


def initializeUltrasonicSensors(gpio_in, gpio_out):
    GPIO.setup(gpio_out, GPIO.OUT)
    GPIO.setup(gpio_in, GPIO.IN)
    GPIO.output(gpio_out, False)
    print('Waiting For Sensor To Settle')
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


def updateObstacles(obstacleBooleans):
    bufferSize = 10
    numSensors = 3

    GPIO.setmode(GPIO.BCM)
    echoTrigPairs = [(13, 19), (5, 6), (17, 27)]
    for echo, trig in echoTrigPairs:
        initializeUltrasonicSensors(echo, trig)

    sensorValues = [[100] * bufferSize for i in range(numSensors)]
    while True:
        for i in range(numSensors):
            sensorValues[i].pop(0)
            sensorValues[i].append(getDistance(*echoTrigPairs[i]))
            average = sum(sensorValues[i]) / bufferSize
            obstacleBooleans[i].value = (average < 60)


def turnLeft(x, y):
    print('Maneuver: Turning left')
    x.value = 255 - 100
    y.value = 0
    time.sleep(2)
    x.value = 0
    y.value = 80
    time.sleep(2)
    x.value = 100
    y.value = 0
    time.sleep(2)


def turnRight(x, y):
    print('Maneuver: Turning right')
    x.value = 100
    y.value = 0
    time.sleep(2)
    x.value = 0
    y.value = 80
    time.sleep(2)
    x.value = 255 - 100
    y.value = 0
    time.sleep(2)


def setJoysticksFromApriltag(x, y, obstacleBooleans):
    resolution = (1920, 1080)
    x_center = resolution[0] / 2
    x_scale = resolution[1] / 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Raspberry Pi IP address, AprilTags UDP port
    sock.bind(('172.20.10.5', 7709))
    lastSeenTime = time.time()
    while True:
        obstacleLeft = obstacleBooleans[0].value
        obstacleCenter = obstacleBooleans[1].value
        obstacleRight = obstacleBooleans[2].value

        # Obstacle left => turn right
        if obstacleLeft and not obstacleRight:
            print('Obstacle on left and NOT right')
            turnRight(x, y)

        # Obstacle right => turn left
        elif obstacleRight and not obstacleLeft:
            print('Obstacle on right and NOT left')
            turnLeft(x, y)

        # Obstacle center but not right => turn right
        elif obstacleCenter and not obstacleRight:
            print('Obstacle on center and NOT right')
            turnRight(x, y)

        # Obstacle center but not left => turn left
        elif obstacleCenter and not obstacleLeft:
            print('Obstacle on center and NOT left')
            turnLeft(x, y)

        elif obstacleCenter:
            print('Obstacles all around')
            obstacleLeft = obstacleBooleans[0].value
            obstacleRight = obstacleBooleans[2].value
            while obstacleLeft and obstacleRight:
                print('Obstacles on both sides... in loop')
                y.value = 255 - 80
                time.sleep(1)
                obstacleLeft = obstacleBooleans[0].value
                obstacleRight = obstacleBooleans[2].value
            print('Leaving loop')
            if obstacleLeft:
                turnRight(x, y)
            else:
                turnLeft(x, y)

        else:
            data, addr = sock.recvfrom(1024)
            if len(data) == 24:
                y.value = 0
                if time.time() - lastSeenTime > 3:
                    x.value = 50
                else:
                    x.value = 0
            elif len(data) == 112:
                lastSeenTime = time.time()

                d = struct.unpack('!8i20f', data)

                width = max(max(abs(d[11] - d[13]), abs(d[13] - d[15])),
                            max(abs(d[15] - d[17]), abs(d[17] - d[11])))
                height = max(max(abs(d[12] - d[14]), abs(d[14] - d[16])),
                            max(abs(d[16] - d[18]), abs(d[18] - d[12])))
                size = max(width, height)
                distanceToAprilTag = 285 / size  # Roughly meters

                if distanceToAprilTag > 1.0:
                    y.value = 50
                    x_val = d[9]
                    if x_val >= x_center:
                        x.value = int((x_val - x_center) * (80 / x_scale))
                    else:
                        x.value = 255 - int((x_center - x_val) * (80 / x_scale))
                elif distanceToAprilTag > 0.85:
                    x.value = 0
                    y.value = 0
                else:
                    y.value = 255 - 50


if __name__ == "__main__":

    x = Value('i', 0)
    y = Value('i', 0)
    obstacleBooleans = (
        Value('b', False), Value('b', False), Value('b', False)
    )

    obstacleProcess = Process(target=updateObstacles,
        args=(obstacleBooleans,))
    obstacleProcess.start()
    time.sleep(3)

    sendJoystickValuesProcess = Process(target=sendJoystickValuesJSMerror,
        args=(x, y))
    sendJoystickValuesProcess.start()

    setJoystickProcess = Process(target=setJoysticksFromApriltag,
        args=(x, y, obstacleBooleans))
    setJoystickProcess.start()

    obstacleProcess.join()
    sendJoystickValuesProcess.join()
    setJoystickProcess.join()
