# This is a Flask app that will serve a captive portal
# to allow users to configure the PiCaster via a web interface on a hotspot

from flask import Flask, render_template, request, redirect
import subprocess
import os
import time

app = Flask(__name__)

CONFIG_FILE = "/etc/picaster.conf"

def load_config():
    # Config file is in format field=value    
    config = {}
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if (line.__contains__("=")):
                key, value = line.strip().split("=")
                config[key] = value    
    return config

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")


print("Starting captive portal...")

# This seems to be unnecessary, but
# Try to delete the existing Hotspot connection but ignore if it doesn't exist
try:
    # Delete the existing connection
    subprocess.run(['nmcli', 'con', 'delete', 'PiCaster-AP'], check=True)
    print("Deleted existing PiCaster-AP connection (if it existed).")
except subprocess.CalledProcessError as e:
    # print(f"Failed to delete existing PiCaster-AP connection: {e}")
    # Do nothing
    pass
    
# This might be unnecessary, but
# Try to deactivate the existing WiFi connection but ignore if it doesn't exist
try:
    # Stop WiFi 
    subprocess.run(['nmcli', 'con', 'down', 'MyWifi'], check=True)
    print("Deactivated MyWifi connection.")
except subprocess.CalledProcessError as e:
    # print(f"Failed to deactivate MyWifi connection: {e}")
    # Do nothing
    pass

# (re)Create the dnsmasq redirect file. 
# Without this, the dns requests will not be redirected to the captive portal
try:
    with open("/etc/NetworkManager/dnsmasq-shared.d/04-captive-portal-redirect.conf", "w") as f:
        f.write("address=/#/10.42.0.1")
    print("Created /etc/NetworkManager/dnsmasq-shared.d/04-captive-portal-redirect.conf")
except Exception as e:
    print(f"Failed to create /etc/NetworkManager/dnsmasq-shared.d/04-captive-portal-redirect.conf: {e}")

# This brings up the hotspot AP
try:
    # Add a new WiFi access point connection
    # nmcli con add con-name PiCaster-AP ifname wlan0 type wifi ssid PiCaster mode ap wifi.band bg wifi.channel 6 ipv4.method shared
    subprocess.run([
        'nmcli', 'con', 'add', 'con-name', 'PiCaster-AP', 'ifname', 'wlan0', 'type', 
        'wifi','ssid','PiCaster','mode','ap','wifi.band','bg','wifi.channel','6',
        'ipv4.method', 'shared']
    , check=True)
        
        
    print("Added new PiCaster-AP connection.")
except subprocess.CalledProcessError as e:
    print(f"Failed to add new PiCaster-AP connection: {e}")

try:
    # Bring up the access point
    subprocess.run(['nmcli', 'con', 'up', 'PiCaster-AP'], check=True)
    print("Activated PiCaster-AP connection.")
except subprocess.CalledProcessError as e:
    print(f"Failed to activate PiCaster-AP connection: {e}")






# Catchall route 302 redirects to / to serve the captive portal
# @app.route("/", defaults={"path": ""})
# @app.route("/<path:path>")
# def catch_all(path):
#     return redirect("/", code=302)

# Generate 204 status code to avoid browser redirecting to the captive portal
@app.route("/generate_204")
@app.route("/gen_204")
def generate_204():    
    return redirect("/", code=302)



# Reply with the captive portal page for any request
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ssid = request.form.get("ssid")
        psk = request.form.get("psk")
        config = load_config()
        config.update(request.form.to_dict())
        save_config(config)
        
        # Update the WiFi connection using nmcli
        try:
            # Delete the existing connection
            subprocess.run(['nmcli', 'con', 'delete', 'MyWifi'], check=True)
            print("Deleted existing MyWifi connection.")
        except subprocess.CalledProcessError as e:
            # print(f"Failed to delete existing MyWifi connection: {e}")
            # Do nothing
            pass

        try:
            # Add a new WiFi connection
            subprocess.run([
                'nmcli', 'con', 'add', 'con-name', 'MyWifi', 'ifname', 'wlan0', 'type', 
                'wifi','ssid', ssid, 'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', psk]
            , check=True)
            print("Added new MyWifi connection.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to add new MyWifi connection: {e}")

    
        # Bring up the WiFi connection
        try:
            subprocess.run(['nmcli', 'con', 'up', 'MyWifi'], check=True)
            print("Activated MyWifi connection.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to activate MyWifi connection: {e}")

        # Wait for the WiFi connection to be established
        time.sleep(5)
        
        # Run install script and reboot
        # os.system("sudo python3 /path/to/install.py")
        os.system("sudo reboot")

    config = load_config()
    return render_template("index.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
