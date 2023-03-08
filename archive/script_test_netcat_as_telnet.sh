#!/bin/bash
#
#this script creates netcat instances to simulate telnet
#message sending
#
#this is the same base port used to simulate
#listening in the python file
base_port=8100
#specify the number of devices to simulate minus 1
#if simulating 29 devices this will be {0..28}
for i in {0..28}
do
    gnome-terminal --tab --title="Netcat port $((base_port+i))" -- bash -c "netcat -l $((base_port+i))"
done