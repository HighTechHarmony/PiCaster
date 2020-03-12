# PiCaster
Scott McGrath
03-27-2019

An audio streaming uplink box for Airtime/LiquidSoap that runs on a Raspberry Pi.  It uses GPIO for a "GO ON/OFF AIR" switch and 2 LEDs. One indicates network connection and the other indicates ON AIR.  For more info refer to the diagrams in the graphics directory.

It has been tested with the following:
Raspberry Pi3 with Raspbian Lite (Stretch)
Behringer U-Control UCA-222
Airtime 2.5.1 (Liquidsoap 1.1.1)

# Installation
* Copy etc/darkice.cfg into your /etc
* Customize darkice.cfg it with your password information for your Airtime stream input
* Copy the contents of root into your /root

# Notes
root/darkice-1.3-custom_wbtvlp_master_stream-works/ contains a home-rolled version of darkice that logs into icecast2 servers with the username "master" instead of "source" (hardcoded).  The modification is done to a line in src/Icecast2.cpp

This was done because:

* Darkice is the only audio device->stream program I could find that supports mp3 (ices2 only does OGG Vorbis, which is broken in our Liquidsoap version).

* Darkice does not support specification of the username in the config file parameters - it is hardcoded to "source".  


