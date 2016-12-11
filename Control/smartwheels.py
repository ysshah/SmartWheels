import sys
import threading
from time import time
from can2RNET import *


def getRNETjoystickFrameID(can_socket):
    """
    Returns: JoyFrame extendedID as text
    TODO: Fix blocking read in recvfrom
    """
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
            d = struct.unpack('!6i2if2f8f9f', data)
            ID = d[6]
            hamming = d[7]
            goodness = d[8]
            C = d[9:11]
            P = d[11:19]
            H = d[19:]

            x = d[9]
            y = d[10]

            topLeft = d[11:13]
            topRight = d[13:15]
            bottomRight = d[15:17]
            bottomLeft = d[17:19]

            width = max(topRight[0] - topLeft[0], bottomRight[0] - bottomLeft[0])
            height = max(bottomLeft[1] - topLeft[1], bottomRight[1] - topRight[1])
            size = max(width, height)
            print('X: {:4.0f}, Y: {:4.0f}, SIZE: {:4.0f}'.format(x, y, size))

            if size < 300:
                print('going forward')
                joystick_y = 50
                if x >= x_center:
                    joystick_x = int((x - x_center) * (80 / x_scale))
                else:
                    joystick_x = 255 - int((x_center - x) * (80 / x_scale))
            else:
                print('stopping')
                joystick_y = 0


if __name__ == "__main__":
    global joystick_x
    global joystick_y
    global rnet_threads_running
    joystick_x = 0
    joystick_y = 0
    rnet_threads_running = True

    can_socket = opencansocket(0)

    # RNET joystick connection
    rnet_joystick_id = getRNETjoystickFrameID(can_socket)

    # Set chair's speed to the lowest setting
    setSpeedRange(can_socket, 0)

    rnet_joystick_frame_raw = build_frame(rnet_joystick_id + "#0000")

    # if len(sys.argv) == 3:
    #     numSent = 0
    #     count = 300
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

    control_thread = threading.Thread(target=control, daemon=True)
    control_thread.start()

    sleep(180)
