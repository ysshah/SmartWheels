# SmartWheels

## Set up the Raspberry Pi

1. Download Raspbian Jessie from [here](https://www.raspberrypi.org/downloads/raspbian/)
2. Mount the image onto an SD card using these [instructions](https://www.raspberrypi.org/documentation/installation/installing-images/)
3. Follow the on-screen instructions to set up Raspberry Pi
4. Run `sudo raspi-config` and set locale, timezone, keyboard (GB => US)
5. Update packages with `sudo apt-get update` followed by `sudo apt-get upgrade`
6. Install git with `sudo apt-get install git`

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

## AprilTags Setup

### RaspiCam

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

### AprilTags

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

## Installing OpenCV and Python

Follow [this OpenCV guide](http://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/) and then [this Python with camera guide](http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/).