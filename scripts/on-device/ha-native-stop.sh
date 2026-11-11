#!/data/data/com.termux/files/usr/bin/bash
H=/data/data/com.termux/files/home; LAB="$H/zuk-ha-native"
PIDFILE="$LAB/run/ha-native.pid"
if [ ! -s "$PIDFILE" ];then echo 'HA_NATIVE_NOT_RUNNING';exit 0;fi
PID=$(cat "$PIDFILE")
if [[ "$PID" =~ ^[0-9]+$ ]] && kill -0 "$PID" 2>/dev/null;then
 CMD=$(tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null)
 if [[ "$CMD" == *homeassistant* ]];then
  kill -TERM "$PID" || exit 4
  echo "HA_STOP_SIGNAL_SENT=$PID"
  # A graceful HA shutdown can take 10+ seconds; do not race the next launch.
  for ((i=1;i<=50;i++)); do
   if ! kill -0 "$PID" 2>/dev/null; then
    echo "HA_STOP_CONFIRMED_PID=$PID"
    exit 0
   fi
   sleep 1
  done
  echo "HA_STOP_TIMEOUT_PID=$PID"
  exit 5
 else echo 'PID_NOT_HOMEASSISTANT';exit 3;fi
else echo 'PID_STALE';fi
