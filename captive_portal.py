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
    # Clean up the keys in the config dictionary
    config = {key.strip(): value.strip() for key, value in config.items()}

    # Returns a dict of field=value pairs
    return config

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")


def get_available_ssids():
    """Scan for available WiFi networks and return a list of SSIDs."""
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi'], capture_output=True, text=True, check=True)
        ssids = result.stdout.splitlines()
        # Remove empty SSIDs and duplicates
        ssids = list(filter(None, set(ssids)))
        # Sort the SSIDs by name
        ssids.sort(reverse=True)

        return ssids
    except subprocess.CalledProcessError as e:
        print(f"Failed to scan for WiFi networks: {e}")
        return []


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

# Configure the hotspot AP connection in NetworkManager
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

# generate_204 is a special URL that Android devices use to check if they are connected to the internet
# Redirect this to / so that the captive portal page is served instead
@app.route("/generate_204")
@app.route("/gen_204")
def generate_204():    
    return redirect("/", code=302)


# Reply with the captive portal page for any request
@app.route("/", methods=["GET", "POST"])
def index():

    ssids = get_available_ssids()   

    if request.method == "POST":
        ssid = request.form.get("ssid")
        psk = request.form.get("psk")
        config = load_config()
        config.update(request.form.to_dict())
        save_config(config)
        
        
        if ssid == "do_not_change":
            print ("SSID is do_not_change")
            wifi_approved = True  # Skip WiFi verification
        else:
            print(f"SSID is {ssid}")
            wifi_approved = False
            
        
            # Delete the old WiFi connection using nmcli
            # try:
            #     # Delete the existing connection
            #     subprocess.run(['nmcli', 'con', 'delete', 'MyWifi'], check=True)
            #     print("Deleted existing MyWifi connection.")
            # except subprocess.CalledProcessError as e:
            #     # print(f"Failed to delete existing MyWifi connection: {e}")
            #     # Do nothing
            #     pass


        # Verify the WiFi connection
        if not wifi_approved:
            try:
                # Either add or modify the WiFi connection, depending...
                print(f"Checking if MyWifi connection exists...")
                result = subprocess.run(['nmcli', '-t', '-f', 'NAME', 'con', 'show'], capture_output=True, text=True, check=True)
                existing_connections = result.stdout.splitlines()

                if 'MyWifi' in existing_connections:
                    print(f"MyWifi connection exists. Modifying the connection with SSID {ssid} and PSK {psk}.")
                    if psk is None or psk == "":
                        # Open network (no PSK)
                        subprocess.run([
                            'nmcli', 'con', 'modify', 'MyWifi', 'wifi.ssid', ssid
                        ], check=True)
                    else:
                        # Secured network
                        subprocess.run([
                            'nmcli', 'con', 'modify', 'MyWifi', 'wifi.ssid', ssid,
                            'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', psk
                        ], check=True)
                else:
                    print(f"MyWifi connection does not exist. Adding a new connection with SSID {ssid} and PSK {psk}.")
                    if psk is None or psk == "":
                        # Open network (no PSK)
                        subprocess.run([
                            'nmcli', 'con', 'add', 'con-name', 'MyWifi', 'ifname', 'wlan0', 'type',
                            'wifi', 'ssid', ssid
                        ], check=True)
                    else:
                        # Secured network
                        subprocess.run([
                            'nmcli', 'con', 'add', 'con-name', 'MyWifi', 'ifname', 'wlan0', 'type',
                            'wifi', 'ssid', ssid, 'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', psk
                        ], check=True)

                print("WiFi connection configured successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to configure MyWifi connection: {e}")

            
            # Bring up the WiFi connection
            wifi_approved = False        
            try:
                print("Activating MyWifi connection...")
                subprocess.run(['nmcli', 'con', 'up', 'MyWifi'], check=True)
                print("Activated MyWifi connection.")
                wifi_approved = True            
            except subprocess.CalledProcessError as e:
                # error_message = "Failed to activate WiFi connection because: " + str(e)
                error_message = "Failed to activate WiFi connection. Please check the configuration and try again."
                print(f"Failed to activate MyWifi connection: {e}")

            # Wait for the WiFi connection to be established
            time.sleep(5)
        

        
        
        # Proceed with install script and reboot only if WiFi is approved
        if wifi_approved:
            success_message = "WiFi connection activated successfully. Rebooting..."
            config = load_config()
            rendered_page = render_template(
                "index.html",
                config=config,                
                ssids=ssids,
                error_message=None,
                success_message=success_message
            )
        
            # Send the rendered page to the user
            with open("/tmp/rendered_page.html", "w") as f:
                f.write(rendered_page)


            # stop the button monitor service so the lights stop flashing
            # DON'T DO THIS! It kills us because we are a child of the button monitor
            # os.system("sudo systemctl stop picaster-button-monitor.service")
            if 'home_path' in config:
                print("Running install script {}/install.py".format(config['home_path']))
            else:
                print("Error: Unable to launch install.py, incorrect path configuration?")
                print("config: ")
                print(config)                
            try:
                # Run install.py from the home_dir location
                config = load_config()
                os.system("sudo python3 {}/install.py -silent".format(config['home_path']))
                print("Install script completed successfully.")                
            except Exception as e:
                print(f"Failed to run install script: {e}")
                error_message = "WARNING: Failed to run install new config. Check the configuration and try again."
                config = load_config()
                rendered_page = render_template(
                    "index.html",
                    config=config,
                    ssids=ssids,
                    error_message=error_message,
                    success_message=None
                )                
                # Send the rendered page to the user
                with open("/tmp/rendered_page.html", "w") as f:
                    f.write(rendered_page)

            
            # If we made it this far, reboot the system
            print("Rebooting...")
            os.system("sudo systemctl reboot --force")            
            time.sleep(5)
            exit(0)
        else:
            print("Skipping install script and reboot due to WiFi activation failure.")


    config = load_config()
    return render_template("index.html", config=config, ssids=ssids, error_message=error_message if "error_message" in locals() else None, success_message=success_message if "success_message" in locals() else None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
