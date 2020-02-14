#!/usr/bin/python

#!/usr/bin/env python
# Purpose: To toggle a GPIO port that shows IP address of your Raspberry Pi in morse code
# Useful for if you do not have a monitor to use with Pi


import RPi.GPIO as GPIO
import os
import subprocess
import time
import sys


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED = 21

GPIO.setup(LED, GPIO.OUT)
GPIO.output(LED, GPIO.LOW)

def main():

    try:
        ip = ''
        time_start = time.time()
        # Constantly searching for valid IP address. Quits if not IP found within 5 minutes
        while ip == '':
	    #print "Starting ifconfig"
            ip = subprocess.check_output("ifconfig | grep \"inet \" | grep broadcast | cut -f10 -d\' \'", shell=True)
#	    print ip
            time_now = time.time()
            time_since_start = time.strftime('%M', time.localtime(time_now - time_start))
            if int(time_since_start) >= 5:
                sys.exit()
        print ip
        # Initialize morse code variable and strip the ip of all newline characters and spaces
        morse = ''
        ip = ip.strip()
        for num in ip:
            morse += str2morse(num)
        # IP address is flashed in morse code after 3 preliminary flashes
        # IMPORTANT! Short HIGH = Dot (1), Long HIGH = Dash (0)
        # Example: 127 = 10000 11000 00111
        for i in range(3):
            GPIO.output(LED, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(LED, GPIO.LOW)
            time.sleep(1)
        for value in morse:
            if value == '1':
                GPIO.output(LED, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(LED, GPIO.LOW)
                time.sleep(.5)
	    elif value == '2':
		time.sleep(.5)
            else:
                GPIO.output(LED, GPIO.HIGH)
                time.sleep(.5)
                GPIO.output(LED, GPIO.LOW)
                time.sleep(.5)

    # If the user presses CTRL-C
    except KeyboardInterrupt:
        GPIO.output(LED, GPIO.LOW)
    finally:
        GPIO.cleanup()


def str2morse(number):
    '''
    This function takes a string input called number (which will only be
    numbers and a period and translate it to morse code
    Dot = 1
    Dash = 0
    '''

    if number == '0':
        return '000002'
    elif number == '1':
        return '100002'
    elif number == '2':
        return '110002'
    elif number == '3':
        return '111002'
    elif number == '4':
        return '111102'
    elif number == '5':
        return '111112'
    elif number == '6':
        return '011112'
    elif number == '7':
        return '001112'
    elif number == '8':
        return '000112'
    elif number == '9':
        return '000012'
    elif number == '.':
        return '101012'

if __name__ == '__main__':
    main()

