#!/bin/bash

# ./kill-all.sh kills all processes

sudo killall -9 tcpdump
sudo killall -9 tor-streamstatus-stem.py
sudo killall -9 tor-kill-streams-stem.py
sudo killall -9 tor-control-stem.py
sudo killall -9 tor-hsConnStatus-stem.py
sudo killall -9 launch-browser.py
sudo killall -9 tor
sudo killall -9 firefox
sudo killall -9 firefox-bin
sudo killall -9 xulrunner-stub*
# Just in case
sudo killall dropbox
