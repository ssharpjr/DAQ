#! /bin/bash

# tail_log_daq.sh - Use tail to follow a log

# Variables (uppercased args)
DEVICE=${1^^}
APP_DIR="/srv/app_daq"
LOG_DIR="$APP_DIR/log"
LOG_FILE="$LOG_DIR/$DEVICE.log"
TAIL="$(which tail)"

# Check args
# $0 = app, $1 = "device"
if [ -z $1 ]; then
  echo ""
  echo "Usage: $0 <DEVICE_ID>"
  echo "Example: $0 PM0021"
  echo ""
  exit 1
fi

# Start Application
echo ""
echo "Showing the tail of the log: $LOG_FILE."
echo "Press CTRL-C to exit"
echo ""
$TAIL -f $LOG_FILE
