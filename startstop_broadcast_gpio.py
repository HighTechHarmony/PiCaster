#!/usr/bin/python

# The purpose of this script is to provide a display/control for the remote broadcaster.
# It monitors the state of the broadcast switch via GPIO. 
# According to this, it either starts the broadcast process or stops it.
# It also changes the state of an on-air light via GPIO, according to whether liquidsoap is connected successfully or not.
# Author: Scott McGrath

import sys
import RPi.GPIO as GPIO
import time
import os
import signal
import re
import subprocess
import threading

# Read config info from a file called picaster.conf
# This file should be in the same directory as this script
# The file should contain at least the following lines:
# address (the address of the server)
# port  (the port number of the server)
# gpio_on_air_light (the gpio address of the red light)
# gpio_on_air_switch (the gpio address of the switch)

# Example values:
# address= "libretime-vm"
# port = 8003
# gpio_on_air_light = 16
# gpio_on_air_switch = 20

config_file = "/etc/picaster.conf"
if not os.path.exists(config_file):
    config_file = "./picaster.conf"


try:
	with open(config_file) as f:
		for line in f:
			if re.search("address", line):
				address = line.split("=")[1].strip()

			if re.search("port", line):
				# Strip quotes and convert to int
				port = int(line.split("=")[1].strip())

			if re.search("gpio_on_air_light", line):
				gpio_on_air_light = int(line.split("=")[1].strip())
			
			if re.search("gpio_on_air_switch", line):
				gpio_on_air_switch = int(line.split("=")[1].strip())

			if re.search("home_path", line):
				home_path = line.split("=")[1].strip()
except:
	print ("Error reading config file: %s" % config_file)
	sys.exit(1)


# Strip any quotes from the read values
address = address.replace('"', '')
home_path = home_path.replace('"', '')

# Name of liquidsoap script is the hostname.ls
liquidsoap_script = home_path + "/" + address + ".ls"

# Flag to track whether we think the broadcast process is running
process_created=0

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Setup the GPIO for the on air light
GPIO.setup(gpio_on_air_light, GPIO.OUT)
GPIO.output(gpio_on_air_light, GPIO.LOW)

# Setup the GPIO for the switch
GPIO.setup(gpio_on_air_switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	
def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
	flashing = False
	time.sleep(1)
	GPIO.output(gpio_on_air_light, GPIO.LOW)
	time.sleep(5)
	GPIO.cleanup(gpio_on_air_light)
	GPIO.cleanup(gpio_on_air_switch)	
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def sigterm_handler(signal, frame):
	print('Received SIGTERM signal')
	flashing = False
	time.sleep(1)
	GPIO.output(gpio_on_air_light, GPIO.LOW)
	time.sleep(.5)
	GPIO.cleanup(gpio_on_air_light)
	GPIO.cleanup(gpio_on_air_switch)	
	sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)

def monitor_liquidsoap_output(process):
	"""Monitor the output of the liquidsoap process for the key phrase."""
	global gpio_on_air_light, flashing
	for line in iter(process.stdout.readline, ''):
		decoded_line = line.strip()
		print(decoded_line)  # Print the output for debugging
		if "Connection setup was successful." in decoded_line:
			flashing = False # Stop the flashing light
			time.sleep(.5)
			GPIO.output(gpio_on_air_light, GPIO.HIGH) # Turn on the on-air light solid
			print("Connection setup was successful. GPIO light turned ON.")
			break

# Simple flashing
# def flash_on_air_light():
#     """Flash the on-air light while waiting for the key phrase."""
#     global flashing
#     while flashing:
#         GPIO.output(gpio_on_air_light, GPIO.HIGH)
#         time.sleep(0.5)
#         GPIO.output(gpio_on_air_light, GPIO.LOW)
#         time.sleep(0.5)		

# Flash wih linearly ramping up rate 
def flash_on_air_light():
    """Flash the on-air light while waiting for the buffering process."""
    global flashing
    start_time = time.time()
    duration = 30  # Ramp-up duration in seconds
    initial_delay = 0.5  # Initial delay for 1 cycle per second
    final_delay = 0.0625  # Final delay for 8 cycles per second

    while flashing:
        elapsed_time = time.time() - start_time
        if elapsed_time > duration:
            delay = final_delay  # After 30 seconds, maintain the fastest rate
        else:
            # Linearly interpolate the delay
            delay = initial_delay - (elapsed_time / duration) * (initial_delay - final_delay)

        GPIO.output(gpio_on_air_light, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(gpio_on_air_light, GPIO.LOW)
        time.sleep(delay)


print("Broadcaster UI running.");

switch_pos = GPIO.input(gpio_on_air_switch)

while True:
	switch_pos = GPIO.input(gpio_on_air_switch)

	# Switch is in the broadcast position
	if switch_pos==0:
		# See if the process died and restart if necessary
		if process_created:
			#print p.poll()
			# Python is so wacky, p.poll() evals to "none" if the process is running, and 0 if it's not.
			if p.poll() == 0:
				print("Detected lost connection, Re-starting broadcast\n")
				try:
					p = subprocess.Popen(["/usr/bin/liquidsoap", liquidsoap_script])
					print ("Liquidsoap process restarted with PID: ", p.pid)
					GPIO.output(gpio_on_air_light, GPIO.HIGH)
					process_created=1
		
				except:
					print("liquidsoap start exception...\n")
					GPIO.output(gpio_on_air_light, GPIO.LOW)
				pass
		elif process_created == 0:
			print("Switched to on-air. Enabling broadcast\n")
			try:
				p = subprocess.Popen(
					["/usr/bin/liquidsoap", liquidsoap_script],
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE,
					bufsize=1,
					universal_newlines=True
				)
				print ("Liquidsoap process started with PID: ", p.pid)
				
				process_created = 1

				# Start flashing the on-air light
				flashing = True
				flash_thread = threading.Thread(target=flash_on_air_light)
				flash_thread.daemon = True
				flash_thread.start()

				# GPIO.output(gpio_on_air_light, GPIO.HIGH)

				# Start a thread to monitor the liquidsoap output
				monitor_thread = threading.Thread(target=monitor_liquidsoap_output, args=(p,))
				monitor_thread.daemon = True
				monitor_thread.start()

			except Exception as e:
				print(f"Liquidsoap start exception: {e}\n")
				GPIO.output(gpio_on_air_light, GPIO.LOW)
			pass


	# Switch is in the standby position
	elif switch_pos == 1:
		# If the process is running, terminate it
		if process_created:
			print("Switched to standby. Disabling broadcast\n")
			try:
				p.terminate()
				p.wait()  # Wait for the process to terminate
				GPIO.output(gpio_on_air_light, GPIO.LOW)  # Turn off the on-air light
				process_created = 0
				flashing = False  # Stop the flashing thread if it is running
			except Exception as e:
				print(f"Exception while stopping liquidsoap: {e}\n")
				pass
		else:
			# Ensure the on-air light is off if the process is not running
			GPIO.output(gpio_on_air_light, GPIO.LOW)

	time.sleep(2)
