# PiCaster

Author: Scott McGrath

This is an audio streaming uplink box for Libretime/Airtime/LiquidSoap/Icecast2 and others that runs on a Raspberry Pi. It uses GPIO for a "GO ON/OFF AIR" switch, a "connect ok" LED, and an "on-air" LED. For more info refer to the diagrams in the graphics directory.

It has been tested with the following components:
Raspberry Pi3 with Raspbian Lite (Bookworm)
Behringer U-Control UCA-222

It has been tested with the following endpoints (AKA, stream consumers):
Airtime 2.5.1
Liquidsoap 1.1.1 and higher
Libretime 4.2.0
Icecast 2.4.4

# Dependencies

- Liquidsoap
- Python3
- ffmpeg
- Pulseaudio or ALSA

# Hardware

Schematic coming soon.

- Connect a switch between VCC, a GPIO (example: 20) and ground
- Connect a "net connect ok" LED between GPIO 16 and ground (220 ohm resistor)
- Connect an "on air" LED between GPIO 21 and ground (220 ohm resistor)
- Connect an audio interface via USB and then identify it

# Installation

- Copy picaster.conf.example to /etc/picaster.conf and edit as appropriate for your setup
- Run the installer as follows:
  `sudo python3 install.sh`

- Enable and start the processes:

```
  sudo systemctl enable picaster-broadcast.service
  sudo systemctl start picaster-broadcast.service
  sudo systemctl enable picaster-connect-test.service
  sudo systemctl start picaster-connect-test.service
```

# Operation

Upon bootup, the picaster-connect-test service will attempt to connect to the configured port and verify that net connectivity is there (nothing else). It will test periodically to ensure this is still the case.

The picaster-broadcast service will monitor the switch.

Switching to the broadcast position will launch liquidsoap. While liquidsoap is starting, the on-air light flash and ramp up in speed. Once liquidsoap has confirmed it is connected and delivering audio, the on-air light will turn solid, and you are good to begin your broadcast.

Switching back to standby will gracefully terminate liquidsoap and the on-air light will extinguish.

# Notes

ALSA is recommended. To identify your hardware address, install `apt install alsa-utils`

Then do: `aplay -l`

Find the first entry that matches your audio hardware, as identified in `lsusb`

This project was started in 2019 and originally used darkice. It has been overhauled to use liquidsoap due to its significantly more robust and versatile nature. However liquidsoap is rather resource intensive, so it is unlikely that this will work well on anything less than a Raspberry Pi 3.
