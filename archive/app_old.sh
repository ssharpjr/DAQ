#! /bin/bash

# Check args
if [ -z $1 ]; then
  echo ""
  echo "ERROR: Missing Device ID argument"
  echo "Usage: $0 <Device_ID>"
  echo ""
  exit 1
fi


# Start application
# /usr/bin/tmux new-session -s "$1" -d && tmux send-keys -t "$1" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID $1 >> /srv/app_daq/log/$1.log" Enter
# /usr/bin/tmux new-session -s "$1" -d && tmux send-keys -t "$1" "cd /srv/app_daq && source env/bin/activate && sudo env/bin/python main.py --deviceID $1" Enter
cd /srv/app_daq && source env/bin/activate && sudo env/bin/python main.py --deviceID $1