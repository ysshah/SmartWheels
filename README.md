# SmartWheels

## Set up the Raspberry Pi

1. Download Raspbian Jessie from [here](https://www.raspberrypi.org/downloads/raspbian/).
2. Mount the image onto an SD card using these [instructions](https://www.raspberrypi.org/documentation/installation/installing-images/).
3. Follow the on-screen instructions to set up Raspberry Pi.
4. Run `sudo raspi-config` and set locale, timezone, keyboard (GB => US).
5. Update packages with `sudo apt-get update` followed by `sudo apt-get upgrade`.
6. Install git with `sudo apt-get install git`.

## R-NET Setup

Clone Stephen Chavez's repository
```
git clone https://github.com/redragonx/can2RNET
```

Install can-utils
```
sudo apt-get install can-utils
```

Add the following lines to /boot/config.txt
```
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
dtoverlay=spi-bcm2835
```

Add the following lines to /etc/network/interfaces
```
allow-hotplug can0
iface can0 can static
    bitrate 125000
    up /sbin/ip link set $IFACE down
    up /sbin/ip link set $IFACE up
```

Add these kernel modules to /etc/modules
```
mcp251x
can_dev
```

Boot with everything connected and run
```
python3 JoyLocal.py
```

## SSH to Raspberry Pi

1. Connect the computer to a WiFi network. Since CalVisitor doesn't support local SSH and AirBears2 is difficult to set up on the Raspberry Pi, we use enable a Personal Hotspot on an iPhone (Settings > Personal Hotspot) to use as our local WiFi network.
2. Connect Raspberry Pi to the same WiFi network using these [instructions](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md).
3. SSH using these [instructions](https://www.raspberrypi.org/documentation/remote-access/ssh/unix.md).
4. (Optional) Set up a permanent IP address for the Raspberry Pi using either this [link](https://www.modmypi.com/blog/how-to-give-your-raspberry-pi-a-static-ip-address-update) or the second comment in this [link](https://www.modmypi.com/blog/tutorial-how-to-give-your-raspberry-pi-a-static-ip-address). Not sure which one did the trick.
5. (Optional) Enable password-less SSH by copying the contents of the computer's id_rsa.pub file to the Raspberry Pi's ~/.ssh/authorized_keys file.

## AprilTags on iPhone to Raspberry Pi

1. Download the [AprilTag application](https://itunes.apple.com/us/app/apriltag/id736108128) on the iPhone.
2. Tap the yellow text on the top left corner to go to settings, enter the Raspberry Pi's IP address into the "UDP Transmit Addr" field, and turn on the "UDP Transmit Enabled" switch.
3. Receive the UDP packets on port 7709 according to the [AprilTags wiki](https://april.eecs.umich.edu/wiki/AprilTags). See their example decoder written in Java [here](https://april.eecs.umich.edu/apriltag/AprilTagReceive.java).

## Discontinued Instructions

### AprilTags on Raspberry Pi

#### RaspiCam

Install OpenCV so that RaspiCam compiles with OpenCV compatibility
```
sudo apt-get install libopencv-dev
```

Clone repository (fixes BGR issues from original [SVN repository](https://sourceforge.net/projects/raspicam/files/))
```
git clone https://github.com/6by9/raspicam-0.1.3
```

Following these [instructions](https://www.uco.es/investiga/grupos/ava/node/40)...
```
cd raspicamxx
mkdir build
cd build
cmake ..
```

Verify that `-- CREATE OPENCV MODULE=1` in the output, then run
```
make
sudo make install
sudo ldconfig
```

#### AprilTags

Following these [instructions](http://people.csail.mit.edu/kaess/apriltags/)...

Install dependencies
```
sudo apt-get install subversion cmake libopencv-dev libeigen3-dev libv4l-dev
```

Clone repository
```
git clone https://github.com/ysshah/SmartWheels.git
```

Compile and run
```
cd SmartWheels
make
./build/bin/apriltags_demo
```

### Installing OpenCV and Python

Follow [this OpenCV guide](http://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/) and then [this Python with camera guide](http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/).
