import sys
import threading
import termios
import tty
import select
from time import time
import RPi.GPIO as GPIO
from can2RNET import *


TRIG1 = 22 #output
ECHO1 = 27 #input
TRIG2 = 6  #output
ECHO2 = 13 #input
TRIG3 = 24 #output
ECHO3 = 23 #input


def getRNETjoystickFrameID(can_socket):
    """
    Returns: JoyFrame extendedID as text
    TODO: Fix blocking read in recvfrom
    """
    ready = select.select([can_socket], [], [], 1.0)
    if ready[0]:
        start = time()
        while (time() - start) < 1:
            cf, addr = can_socket.recvfrom(16)
            frameid = dissect_frame(cf).split('#')[0]
            if frameid[:3] == '020':
                return frameid
    raise TimeoutError('No RNET-Joystick frame seen')


def setSpeedRange(cansocket,speed_range):
    """Set speed_range from 0% - 100%."""
    if 0 <= speed_range and speed_range <= 100:
        cansend(cansocket,'0a040100#{:02x}'.format(speed_range))
    else:
        print('Invalid RNET SpeedRange: {}'.format(speed_range))


def inject_rnet_joystick_frame(can_socket, rnet_joystick_id):
    """Wait for joyframe and inject another spoofed frame ASAP."""
    # Prebuild the frame we are waiting on
    rnet_joystick_frame_raw = build_frame(rnet_joystick_id + '#0000')
    while rnet_threads_running:
        cf, addr = can_socket.recvfrom(16)
        if cf == rnet_joystick_frame_raw:
            cansend(can_socket, '{}#{:02x}{:02x}'.format(
                rnet_joystick_id, joystick_x, joystick_y))


def initializeUltrasonicSensors(gpio_in, gpio_out):
    GPIO.setup(gpio_out,GPIO.OUT)
    GPIO.setup(gpio_in,GPIO.IN)

    GPIO.output(gpio_out, False)
    print("Waiting For Sensor To Settle")
    time.sleep(1)


def getDistance(gpio_in, gpio_out, ultrasound):
    global distance1
    global distance2
    global distance3
    GPIO.output(gpio_out, True)
    time.sleep(0.00001)
    GPIO.output(gpio_out, False)
    while GPIO.input(gpio_in)==0:
        pulse_start = time.time()

    while GPIO.input(gpio_in)==1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150

    distance = round(distance, 2)
    if (ultrasound == 1):
        distance1 = round(distance, 2)
        #print("Distance1: " + str(distance1))
    elif (ultrasound == 2):
        distance2 = round(distance, 2)
        #print("Distance2: " + str(distance2))
    elif (ultrasound == 3):
        distance3 = round(distance, 2)

    #print("Sensor" + str(ultrasound) + "Distance: " +  ":" + str(distance) + " cm",)
    time.sleep(0.1)


def control():
    global joystick_x
    global joystick_y

    resolution = (1920, 1080)
    x_center = resolution[0] / 2
    x_scale = resolution[0] / 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Raspberry Pi IP address, AprilTags UDP port
    sock.bind(('172.20.10.5', 7709))
    while True:
        data, addr = sock.recvfrom(1024)
        if len(data) == 24:
            print('No tags')
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
                joystick_y = 50
                x = d[9]
                if x >= x_center:
                    joystick_x = int((x - x_center) * (80 / x_scale))
                else:
                    joystick_x = 255 - int((x_center - x) * (80 / x_scale))
            elif size < 400:
                print('stopping')
                joystick_x = 0
                joystick_y = 0
            else:
                print('going backwards')
                joystick_y = 255 - 50


def manualOverride():
    global joystick_x
    global joystick_y
    global rnet_threads_running

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    while True:
        char = getch()
        if char == 'w':
            joystick_y = 127
        elif char == 'd':
            joystick_x = 127
        elif char == 'a':
            joystick_x = 255 - 127
        elif char == 's':
            joystick_y = 255 - 127
        elif char == 'x':
            joystick_x = 0
            joystick_y = 0
            rnet_threads_running = False
            break
        char = ''
        sleep(0.2)
        joystick_x = 0
        joystick_y = 0


if __name__ == "__main__":
    global joystick_x
    global joystick_y
    global distance1
    global distance2
    global distance3
    global rnet_threads_running
    joystick_x = 0
    joystick_y = 0
    distance1 = 0
    distance2 = 0
    distance3 = 0
    rnet_threads_running = True

    GPIO.setmode(GPIO.BCM)
    initializeUltrasonicSensors(ECHO1, TRIG1)
    initializeUltrasonicSensors(ECHO2, TRIG2)
    initializeUltrasonicSensors(ECHO3, TRIG3)

    can_socket = opencansocket(0)

    # RNET joystick connection
    rnet_joystick_id = getRNETjoystickFrameID(can_socket)

    # Set chair's speed to the lowest setting
    setSpeedRange(can_socket, 0)

    # if len(sys.argv) == 4:
    #     rnet_joystick_frame_raw = build_frame(rnet_joystick_id + "#0000")
    #     numSent = 0
    #     count = int(sys.argv[3])
    #     while numSent < count:
    #         cf, addr = can_socket.recvfrom(16)
    #         if cf == rnet_joystick_frame_raw:
    #             numSent += 1
    #             # print('sending on index {}'.format(i)))
    #             cansend(can_socket, '{}#{:02x}{:02x}'.format(
    #                 rnet_joystick_id, int(sys.argv[1]), int(sys.argv[2])))
    #     print('sent {} times'.format(count))

    inject_rnet_joystick_frame_thread = threading.Thread(
        target=inject_rnet_joystick_frame,
        args=(can_socket, rnet_joystick_id,),
        daemon=True)
    inject_rnet_joystick_frame_thread.start()

    if len(sys.argv) == 1 or sys.argv[1] != '-m':
        print('Autonomous control mode enabled')
        control_thread = threading.Thread(target=control, daemon=True)
    else:
        print('Manual override mode enabled')
        control_thread = threading.Thread(target=manualOverride, daemon=True)

    control_thread.start()

    while rnet_threads_running:
        sleep(0.5)
