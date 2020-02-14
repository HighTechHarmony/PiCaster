#!/bin/sh

PID=`pidof darkice`

echo "Killing darkice pid $PID"
/bin/kill $PID

