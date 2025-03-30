import RPi.GPIO as GPIO
import time
import os
import re
import threading
import sys
import signal
import subprocess

# Timing
BUTTON_HOLD_SECONDS = 4


# Read the necessary values from the config file
config_file = "/etc/picaster.conf"
if not os.path.exists(config_file):
    config_file = "./picaster.conf"

gpio_setup_button = 0
gpio_net_connect_ok_light = 0
gpio_on_air_light = 0

try:
    with open(config_file) as f:
        for line in f:
            if re.search("gpio_net_connect_ok_light", line):
                gpio_net_connect_ok_light = int(line.split("=")[1].strip())
                    
            if re.search("gpio_setup_button", line):
                gpio_setup_button = int(line.split("=")[1].strip())
            
            if re.search("gpio_on_air_light", line):
                gpio_on_air_light = int(line.split("=")[1].strip())

            if re.search("home_path", line):
                home_path = line.split("=")[1].strip()

except:
	print ("Error reading config file: %s" % config_file)
	sys.exit(1)

if gpio_net_connect_ok_light == 0 or gpio_setup_button == 0 or gpio_net_connect_ok_light == 0:
	print ("Error reading config file, missing values")
	sys.exit(1)



# Setup GPIO
LED_PINS = [gpio_net_connect_ok_light, gpio_on_air_light]  # GPIO pins for the LEDs


try:
    # GPIO.setmode(GPIO.BCM)
    # for pin in LED_PINS:
    #     # print ("Setting up pin %d" % pin) 
    #     GPIO.setup(pin, GPIO.OUT)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_setup_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except:
    # If this fails it is most likely because there are other picaster processes that have not been stopped
    # print ("Error setting up lights GPIO. Make sure there are no other picaster processes running")
    print ("Couldn't set up button GPIO") 
    sys.exit(1)



# Signal handler for Ctrl+C
def signal_handler(signal, frame):
    global gpio_net_connect_ok_light
    global gpio_on_air_light
    global gpio_setup_button

    print('You pressed Ctrl+C!')
    # Turn off the light in case it was on
    GPIO.output(gpio_net_connect_ok_light, GPIO.LOW)
    GPIO.output(gpio_on_air_light, GPIO.LOW)
    time.sleep (1)
    GPIO.cleanup(gpio_net_connect_ok_light)
    GPIO.cleanup(gpio_on_air_light)
    print ("Clean up GPIO\n")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Another signal handler for the termination signal by systemd
def sigterm_handler(signal, frame):
    global gpio_net_connect_ok_light
    global gpio_on_air_light
    global gpio_setup_button

    print('Received SIGTERM signal')
    GPIO.output(gpio_net_connect_ok_light, GPIO.LOW)
    GPIO.output(gpio_on_air_light, GPIO.LOW)
    time.sleep (1)
    GPIO.cleanup(gpio_net_connect_ok_light)
    GPIO.cleanup(gpio_on_air_light)
    GPIO.cleanup(gpio_setup_button)
    print ("Clean up GPIO\n")
    sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)





import threading

def flash_leds():
    """Flash LEDs to indicate setup mode."""
    # Setup GPIO for LEDs
    GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
    for pin in LED_PINS:
        GPIO.setup(pin, GPIO.OUT)  # Set each LED pin as an output

    def flash():
        while True:  # Flash indefinitely
            for pin in LED_PINS:
                GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.5)
            for pin in LED_PINS:
                GPIO.output(pin, GPIO.LOW)
            time.sleep(0.5)

    # Start flashing in a separate thread
    flash_thread = threading.Thread(target=flash, daemon=True)
    flash_thread.start()


def shutdown_broadcast_services():
    """Shutdown existing services."""
    print("Shutting down broadcast services...")
    os.system('sudo systemctl stop picaster-broadcast.service || true')
    os.system('sudo systemctl stop picaster-connect-test.service || true')

def start_captive_portal():
    """Start WiFi hotspot and captive portal."""
    print(f"Starting captive portal {home_path}/captive_portal.py...")
    try:
        os.system(f'sudo python3 {home_path}/captive_portal.py')
    except Exception as e:
        print(f"Failed to start captive_portal.py: {e}")


try:
    button_pressed_time = None
    prev_button_pressed_duration = -1

    # This loop will run indefinitely until the button is held for BUTTON_HOLD_SECONDS
    while True:
        # Wait for button press
        if GPIO.input(gpio_setup_button) == GPIO.LOW:
            # print ("Button pressed")
            if button_pressed_time is None:
                button_pressed_time = time.time()

            # Check if button is held for required duration
            if time.time() - button_pressed_time >= BUTTON_HOLD_SECONDS:
                break
                
                
            else:
                button_pressed_duration = time.time() - button_pressed_time
                if int(prev_button_pressed_duration) != int(button_pressed_duration):
                    print("Button pressed for %d seconds" % button_pressed_duration)
                    prev_button_pressed_duration = button_pressed_duration
        else:
            button_pressed_time = None

        time.sleep(0.1)
    
    # Things to do when setup mode is activated
    print("Setup mode activated.")
    shutdown_broadcast_services()           
    flash_leds()
    start_captive_portal()    

    # At this point, control is handed off to the captive portal server, so there is nothing left to do
    # We do keep the program alive for the LEDs to keep flashing
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
