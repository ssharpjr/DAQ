#!/bin/bash

tmux new-session -d -s "PM0021"
tmux send-keys -t "PM0021" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0021" Enter

tmux new-session -d -s "PM0022"
tmux send-keys -t "PM0022" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0022" Enter

tmux new-session -d -s "PM0023"
tmux send-keys -t "PM0023" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0023" Enter

tmux new-session -d -s "PM0024"
tmux send-keys -t "PM0024" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0024" Enter

tmux new-session -d -s "PM0025"
tmux send-keys -t "PM0025" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0025" Enter

tmux new-session -d -s "PM0026"
tmux send-keys -t "PM0026" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0026" Enter

tmux new-session -d -s "PM0027"
tmux send-keys -t "PM0027" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0027" Enter

tmux new-session -d -s "PM0028"
tmux send-keys -t "PM0028" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0028" Enter

tmux new-session -d -s "PM0029"
tmux send-keys -t "PM0029" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0029" Enter

tmux new-session -d -s "PM0030"
tmux send-keys -t "PM0030" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0030" Enter

tmux new-session -d -s "PM0031"
tmux send-keys -t "PM0031" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0031" Enter

tmux new-session -d -s "PM0032"
tmux send-keys -t "PM0032" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0032" Enter

tmux new-session -d -s "PM0033"
tmux send-keys -t "PM0033" "cd /srv/app_daq && source env/bin/activate && env/bin/python main.py --deviceID=PM0033" Enter
