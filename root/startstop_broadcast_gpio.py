#!/usr/bin/python

# The purpose of this script is to provide a rudimentary display/control for the remote broadcaster.
# Author: Scott McGrath

import sys
import RPi.GPIO as GPIO
import time
import os
import signal
import socket
import subprocess

print("sys.version:")
print(sys.version + "\n")

print("GPIO.VERSION: " + GPIO.VERSION)
print("GPIO.RPI_INFO['P1_REVISION'] = " + str(GPIO.RPI_INFO['P1_REVISION']));

io16 = 16
io20 = 20

# Flag to track whether we think the broadcast process is running
process_created=0

# GPIO setup
GPIO.setmode(GPIO.BCM)

# io16 is the green light
GPIO.setup(io16, GPIO.OUT)
GPIO.output(io16, GPIO.LOW)

# io20 is the switch
GPIO.setup(io20, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	
def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
	GPIO.cleanup(io16)
	GPIO.cleanup(io20)
	print ("Clean up GPIO\n")
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)




print("Broadcaster UI running.");

switch_pos = GPIO.input(io20)

while True:
	switch_pos = GPIO.input(io20)

	# Switch is in the broadcast position
	if switch_pos==0:
		# See if the process died and restart if necessary
		if process_created:
			#print p.poll()
			# Python is so wacky, p.poll() evals to "none" if the process is running, and 0 if it's not.
			if p.poll() == 0:
				print "Detected lost connection, Re-starting broadcast\n"
				try:
#	        	               	p = subprocess.Popen(["/usr/bin/ices2", "/etc/ices.xml"])
	        	               	p = subprocess.Popen(["/usr/bin/darkice", "/etc/darkice.cfg"])
                        		print p.pid
					GPIO.output(io16, GPIO.HIGH)
					process_created=1
		
				except:
					print "Darkice start exception...\n"
					GPIO.output(io16, GPIO.LOW)
				pass
		# Start up the broadcast normally
		elif process_created == 0:
                        print "Enabling broadcast\n"
                        try:
#                                p = subprocess.Popen(["/usr/bin/ices2", "/etc/ices.xml"])
                                p = subprocess.Popen(["/usr/bin/darkice", "/etc/darkice.cfg"])
                                print p.pid
	                        GPIO.output(io16, GPIO.HIGH)
                                process_created=1
                
                        except:
                                print "Darkice start exception...\n"
                        pass

			

	# Switch is in the standby position and we think it is running
       	elif process_created:
		print "Disabling broadcast\n"
		try:
			p.terminate()
			GPIO.output(io16, GPIO.LOW)
			process_created=0
		except:
			print "Exception, Darkice is probably already stopped or not started...\n"
			pass

	time.sleep (2)


