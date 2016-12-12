import RPi.GPIO as GPIO
import os
import time
import threading
from threading import Thread, current_thread

GPIO.setmode(GPIO.BCM)

TRIG1 = 22 #output 
ECHO1 = 27 #input
TRIG2 = 23 #output
ECHO2 = 24 #input
TRIG3 = 06 #output 
ECHO3 = 13 #input
distance1 = 0
distance2 = 0
distance3 = 0

def get_ultrasound_distance(gpio_in, gpio_out, ultrasound): 
    #print "Distance Measurement for ultrasound " + str(ultrasound) + " In Progress"
    ident = current_thread().getName()
    GPIO.setup(gpio_out,GPIO.OUT)
    GPIO.setup(gpio_in,GPIO.IN)
    GPIO.setup(gpio_in,GPIO.IN)
    global distance1
    global distance2
    global distance3

    GPIO.output(gpio_out, False)

    #print "Waiting For Sensor To Settle"
    time.sleep(2)

    while True: 
        GPIO.output(gpio_out, True)
        time.sleep(0.00001)
        GPIO.output(gpio_out, False)
        while GPIO.input(gpio_in)==0:
          pulse_start = time.time()

        while GPIO.input(gpio_in)==1:
          pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 17150
        thread_id = int(ident)
        if (thread_id == 1): 
            distance1 = round(distance, 2)
            #print "Distance1: " + str(distance1)
        elif (thread_id == 2): 
            distance2 = round(distance, 2) 
            #print "Distance2: " + str(distance2)
        elif (thread_id == 3): 
            distance3 = round(distance, 2) 
            #print "Distance3: " + str(distance3)
        time.sleep(0.1)
        #time.sleep(0.2)
        #time.sleep(0.3)
        #time.sleep(0.4)

    GPIO.cleanup()

#SCRIPT
ultrasound_1_thread = threading.Thread(target = get_ultrasound_distance, name=1, args = (ECHO1, TRIG1, 1,))
ultrasound_2_thread = threading.Thread(target = get_ultrasound_distance, name=2, args = (ECHO2, TRIG2, 2,))
ultrasound_3_thread = threading.Thread(target = get_ultrasound_distance, name=3, args = (ECHO3, TRIG3, 3,))
ultrasound_1_thread.start()
ultrasound_2_thread.start()
ultrasound_3_thread.start()
while True:
    print "Distance1: " + str(distance1)
    print "Distance2: " + str(distance2)
    print "Distance3: " + str(distance3)
    time.sleep(0.2)
    

