import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

TRIG1 = 22 #output
ECHO1 = 27 #input
TRIG2 = 06 #output
ECHO2 = 13 #input
TRIG3 = 24 #output
ECHO3 = 23 #input
distance1 = 0
distance2 = 0
distance3 = 0


def init_ultra(gpio_in, gpio_out):
    GPIO.setup(gpio_out,GPIO.OUT)
    GPIO.setup(gpio_in,GPIO.IN)

    GPIO.output(gpio_out, False)
    print "Waiting For Sensor To Settle"
    time.sleep(1)

def get_dist(gpio_in, gpio_out, ultrasound):
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
        #print "Distance1: " + str(distance1)
    elif (ultrasound == 2):
        distance2 = round(distance, 2)
        #print "Distance2: " + str(distance2)
    elif (ultrasound == 3):
        distance3 = round(distance, 2)


    #print "Sensor" + str(ultrasound) + "Distance: " +  ":" + str(distance) + " cm",
    time.sleep(0.1)


print "Distance Measurement In Progress"
init_ultra(ECHO1, TRIG1)
init_ultra(ECHO2, TRIG2)
init_ultra(ECHO3, TRIG3)
while True:
    get_dist(ECHO1, TRIG1, 1)
    print "Distance1: " + str(distance1)
    get_dist(ECHO2, TRIG2, 2)
    print "Distance2: " + str(distance2)
    get_dist(ECHO3, TRIG3, 3)
    print "Distance3: " + str(distance3)
    print ""
GPIO.cleanup()
