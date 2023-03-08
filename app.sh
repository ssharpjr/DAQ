#! /bin/bash

# app.sh - Launch app

# Variables (uppercased args)
DEVICE=${2^^}
APP="main.py"
APP_DIR="/srv/app_daq"
LOG_DIR="$APP_DIR/log"
LOG_FILE="$LOG_DIR/$DEVICE.log"
APP_ENV="$APP_DIR/env/bin"
APP_PYTHON="$APP_DIR/env/bin/python"

# Check args
# $0 = app, $1 = "-d", $2 = "device"
if [ -z $1 ] || [ -z $2 ]; then
  # clear
  echo ""
  cd $APP_DIR && source $APP_ENV/activate && sudo $APP_PYTHON $APP -h
  echo ""
  exit 1
fi

# Start application
# clear
cd $APP_DIR
echo "Starting App. Check $LOG_FILE for details (tail -f $LOG_FILE)."
cd $APP_DIR && source $APP_ENV/activate && sudo $APP_PYTHON $APP -d $DEVICE
