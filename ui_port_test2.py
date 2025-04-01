#!/usr/bin/python

import os
import RPi.GPIO as GPIO
import socket
import re
import sys
import time
import signal


# The purpose of this script is to provide an indication as to whether
# the remote broadcaster is able to connect to the server or not.
# It does not remain connnected, it just checks every 15 seconds whether this is possible.


# Read config info from a file called picaster.conf
# The script requires at least the following:
# address (the address of the server)
# port (the port number of the server)
# gpio_net_connect_ok_light (the gpio address of the green light)
# 
# Example values:
# address= "libretime-vm"
# port = 8003
# gpio_net_connect_ok_light = 16

config_file = "/etc/picaster.conf"
if not os.path.exists(config_file):
    config_file = "./picaster.conf"

address = ""
port = 0
gpio_net_connect_ok_light = 0

try:
	with open(config_file) as f:
		for line in f:
			if re.search("address", line):
				address = line.split("=")[1].strip()

			if re.search("port", line):
				# Strip quotes and convert to int
				port = int(line.split("=")[1].strip())

			if re.search("gpio_net_connect_ok_light", line):
				gpio_net_connect_ok_light = int(line.split("=")[1].strip())
				

except:
	print ("Error reading config file: %s" % config_file)
	sys.exit(1)

# Strip quotes from read values
address = address.replace('"', '')


if address == "" or port == 0 or gpio_net_connect_ok_light == 0:
	print ("Error reading config file, missing values")
	sys.exit(1)

# Signal handler for Ctrl+C
def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
		# Turn off the light in case it was on
        GPIO.output(gpio_net_connect_ok_light, GPIO.LOW)
        time.sleep (1)
        GPIO.cleanup(gpio_net_connect_ok_light)
        print ("Clean up GPIO\n")
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Another signal handler for the termination signal by systemd
def sigterm_handler(signal, frame):
	print('Received SIGTERM signal')
	GPIO.output(gpio_net_connect_ok_light, GPIO.LOW)
	time.sleep (1)
	GPIO.cleanup(gpio_net_connect_ok_light)
	print ("Clean up GPIO\n")
	sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)



# GPIO setup
GPIO.setmode(GPIO.BCM)

# gpio_net_connect_ok_light is the gpio address of the green light
GPIO.setup(gpio_net_connect_ok_light, GPIO.OUT)


def check_server(address, port):
    # Create a TCP socket
    s = socket.socket()
    s.settimeout(5)  # Set timeout to 5 seconds
    print("Attempting to connect to %s on port %s" % (address, port))
    try:
        s.connect((address, port))
        print("Connected to %s on port %s" % (address, port))
        s.close()
        return True
    except (socket.timeout, socket.error) as e:
        print("Connection to %s on port %s failed: %s" % (address, port, e))
        return False

while True:
	if check_server (address, port):
		GPIO.output(gpio_net_connect_ok_light, GPIO.HIGH)
	else:
		GPIO.output(gpio_net_connect_ok_light, GPIO.LOW)
	time.sleep(10)


