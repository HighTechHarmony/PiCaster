#/usr/bin/python3

# Reads values from picaster.conf config file and generates various files:
# a LiquidScript file
# systemd service files

import argparse
import os
import re
import sys
import shutil


# This will try to open the file /etc/picaster.conf
# If that fails, it will try to open it in the current directory
config_file = "/etc/picaster.conf"
if not os.path.exists(config_file):
    config_file = "./picaster.conf"

# This script expects the following values in the config file:

# address = host.name.com
# port = 8003
# sound_device = hw:1,0
# mountname = mountname
# input_type = alsa or pulseaudio
# streamuser = user
# streampassword = password
# home = /home/user
# runasuser = user

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Install PiCaster services.")
parser.add_argument(
    "-silent",
    action="store_true",
    help="Run the script in silent mode, skipping any prompts or questions."
)
args = parser.parse_args()

# Check if silent mode is enabled
silent_mode = args.silent
if silent_mode:
    print("Running in silent mode. No prompts will be displayed.")

try:
    with open(config_file) as f:
        for line in f:
            if re.search("address", line):
                address = line.split("=")[1].strip()

            if re.search("port", line):
                # Strip quotes and convert to int
                port = int(line.split("=")[1].strip())

            if re.search("sound_device", line):
                sound_device = line.split("=")[1].strip()

            if re.search("mountname", line):
                mountname = line.split("=")[1].strip()

            if re.search("input_type", line):
                input_type = line.split("=")[1].strip()

            if re.search("streamuser", line):
                streamuser = line.split("=")[1].strip()
            
            if re.search("streampassword", line):
                streampassword = line.split("=")[1].strip()
            
            if re.search("home_path", line):
                home_path = line.split("=")[1].strip()

            if re.search("runasuser", line):
                runasuser = line.split("=")[1].strip()

    # Check for missing values
    required_values = {
        "address": address,
        "port": port,
        "sound_device": sound_device,
        "mountname": mountname,
        "input_type": input_type,
        "streamuser": streamuser,
        "streampassword": streampassword,
        "home_path": home_path,
        "runasuser": runasuser,
    }

    for key, value in required_values.items():
        if not value:
            print(f"Error: Missing required configuration value for '{key}'. Please check the config file.")
            sys.exit(1)

except Exception as e:
    print(f"Error reading config file: {config_file}. Exception: {e}")
    sys.exit(1)

# Strip any quotes from the read values
address = address.replace('"', '')
sound_device = sound_device.replace('"', '')
mountname = mountname.replace('"', '')
input_type = input_type.replace('"', '')
streamuser = streamuser.replace('"', '')
streampassword = streampassword.replace('"', '')
home_path = home_path.replace('"', '')

# Generate the LiquidScript file in the format of:
# output.icecast(%mp3,
#    host = "192.168.15.186", port = 8000,
#    password = "testme", mount = "mp3_128",
#    input.pulseaudio(device="2"))

# Sanitize the address to create a valid filename
sanitized_address = re.sub(r'[^\w\-_\.]', '_', address)


with open(home_path + "/" + sanitized_address + ".ls", "w") as output_file:
    output_file.write(
        "output.icecast(%%mp3,\n    host = \"%s\", port = %d,\n" % (address, port)
    )
    output_file.write(
        "    user = \""+ streamuser + "\",\n"
    )
    output_file.write(
        "    password = \""+ streampassword + "\", mount = \"" + mountname + "\",\n"
    )
    output_file.write(
        "    input."+input_type+"(device=\"%s\"))\n" % sound_device
    )
    
    output_file.close()

# Generate the systemd service file in the format of:
# [Unit]
# Description=PiCaster streamer process
# After=network-online.target
# Wants=network-online.target

# [Service]
# Type=simple
# User=user
# Group=user
# WorkingDirectory=/home/user
# ExecStart=/usr/bin/env bash -c 'exec /usr/bin/python3 /home/user/startstop_broadcast_gpio.py'
# Restart=always
# RestartSec=5

# [Install]
# WantedBy=multi-user.target


with open(home_path + "/picaster-broadcast.service", "w") as output_file:
    output_file.write(
        "[Unit]\nDescription=PiCaster streamer process\nAfter=network-online.target\nWants=network-online.target\n\n"
    )
    output_file.write(
        "[Service]\nType=simple\nUser=%s\nGroup=%s\nWorkingDirectory=%s\n" % (runasuser, runasuser, home_path)
    )
    output_file.write(
        "ExecStart=/usr/bin/env bash -c 'exec /usr/bin/python3 %s/startstop_broadcast_gpio.py'\n" % home_path
    )
    output_file.write(
        "Restart=always\nRestartSec=5\n\n"
    )
    output_file.write(
        "[Install]\nWantedBy=multi-user.target\n"
    )
    output_file.close()


with open(home_path + "/picaster-connect-test.service", "w") as output_file:
    output_file.write(
        "[Unit]\nDescription=PiCaster network connection test\nAfter=network-online.target\nWants=network-online.target\n\n"
    )
    output_file.write(
        "[Service]\nType=simple\nUser=%s\nGroup=%s\nWorkingDirectory=%s\n" % (runasuser, runasuser, home_path)
    )
    output_file.write(
        "ExecStart=/usr/bin/env bash -c 'exec /usr/bin/python3 %s/ui_port_test2.py'\n" % home_path
    )
    output_file.write(
        "Restart=always\nRestartSec=5\n\n"
    )
    output_file.write(
        "[Install]\nWantedBy=multi-user.target\n"
    )
    output_file.close()

with open(home_path + "/picaster-button-monitor.service", "w") as output_file:
    output_file.write(
        "[Unit]\nDescription=PiCaster reset button monitor\nAfter=network-online.target\nWants=network-online.target\n\n"
    )
    output_file.write(
        "[Service]\nType=simple\nUser=%s\nGroup=%s\nWorkingDirectory=%s\n" % (runasuser, runasuser, home_path),
    )
    output_file.write(
        "ExecStart=/usr/bin/env bash -c 'exec /usr/bin/python3 %s/button_monitor.py'\n" % home_path
    )
    output_file.write(
        "Restart=always\nRestartSec=5\n\n"
    )
    output_file.write(
        "[Install]\nWantedBy=multi-user.target\n"
    )
    output_file.close()

# A service unit that disables the AP at bootup, in case it is running
# Needs to have After=network.target NetworkManager.service
with open(home_path + "/picaster-ap-disable.service", "w") as output_file:
    output_file.write(
        "[Unit]\nDescription=Disable the PiCaster-AP NetworkManager Connection at Boot\nAfter=network.target NetworkManager.service\n\n"
    )
    output_file.write(
        "[Service]\nType=oneshot\nExecStart=/usr/bin/nmcli con down \"PiCaster-AP\"\nRemainAfterExit=no\n\n"
    )
    output_file.write(
        "[Install]\nWantedBy=multi-user.target\n"
    )
    output_file.close()



# Copy the service file to /etc/systemd/system
try:
    target_path = "/etc/systemd/system/picaster-broadcast.service"
    print(f"Copying picaster-broadcast.service file to {target_path}...")
    shutil.copy(home_path + "/picaster-broadcast.service", target_path)
    print("Service file copied successfully.")

    target_path = "/etc/systemd/system/picaster-connect-test.service"
    print(f"Copying picaster-connect-test.service file to {target_path}...")
    shutil.copy(home_path + "/picaster-connect-test.service", target_path)
    print("Service file copied successfully.")

    target_path = "/etc/systemd/system/picaster-button-monitor.service"
    print(f"Copying picaster-button-monitor.service file to {target_path}...")
    shutil.copy(home_path + "/picaster-button-monitor.service", target_path)
    print("Service file copied successfully.")

    target_path = "/etc/systemd/system/picaster-ap-disable.service"
    print(f"Copying picaster-ap-disable.service file to {target_path}...")
    shutil.copy(home_path + "/picaster-ap-disable.service", target_path)
    print("Service file copied successfully.")


    # Reload systemd to recognize the new service
    os.system("sudo systemctl daemon-reload")
    # print("Systemd reloaded. You can now enable and start the services using:")
    # print("  sudo systemctl enable picaster-broadcast.service")
    # print("  sudo systemctl start picaster-broadcast.service")
    # print("  sudo systemctl enable picaster-connect-test.service")
    # print("  sudo systemctl start picaster-connect-test.service")

    # Enable and restart the services
    os.system("sudo systemctl enable picaster-broadcast.service")
    os.system("sudo systemctl start picaster-broadcast.service")
    os.system("sudo systemctl enable picaster-connect-test.service")
    os.system("sudo systemctl start picaster-connect-test.service")
    os.system("sudo systemctl enable picaster-button-monitor.service")
    os.system("sudo systemctl start picaster-button-monitor.service")
    os.system("sudo systemctl enable picaster-ap-disable.service")

except PermissionError:
    print("Error: Root privileges are required to copy the service files to /etc/systemd/system.")
    print("Please run this script as root or use sudo.")
    sys.exit(1)

except Exception as e:
    print(f"An error occurred while copying the service file: {e}")
    sys.exit(1)