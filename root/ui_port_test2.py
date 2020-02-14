#!/usr/bin/python

import RPi.GPIO as GPIO
import socket
import re
import sys
import time
import signal

address= "204.13.40.147"
port = 8003
io21 = 21

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        #GPIO.cleanup(io16)
        #GPIO.cleanup(io20)
        GPIO.cleanup(io21)
        print ("Clean up GPIO\n")
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# GPIO setup
GPIO.setmode(GPIO.BCM)

# io21 is the red light
GPIO.setup(io21, GPIO.OUT)
#time.sleep(1)
#GPIO.output(io21, GPIO.LOW)





def check_server(address, port):
	# Create a TCP socket
	s = socket.socket()
	print "Attempting to connect to %s on port %s" % (address, port)
	try:
		s.connect((address, port))
		print "Connected to %s on port %s" % (address, port)
		s.close()
		return True
	except socket.error, e:
		print "Connection to %s on port %s failed: %s" % (address, port, e)
		return False


while True:
	if check_server (address, port):
		GPIO.output(io21, GPIO.HIGH)
	else:
		GPIO.output(io21, GPIO.LOW)
	time.sleep(15)


