#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail
P=/data/data/com.termux/files/usr
H=/data/data/com.termux/files/home
LAB="$H/zuk-ha-native"; V="$LAB/venv-ha"; C="$LAB/config-ha"
export PREFIX="$P" HOME="$H" PATH="$P/bin:/system/bin" TMPDIR="$P/tmp"
export LD_LIBRARY_PATH="$P/lib" UV_CACHE_DIR="$LAB/uv-cache" UV_LINK_MODE=copy
unset LD_PRELOAD
mkdir -p "$LAB/run" "$LAB/logs" "$C"
LOG="$LAB/logs/ha-native-service.log"; PIDFILE="$LAB/run/ha-native.pid"
exec >> "$LOG" 2>&1
printf '\nHA_SERVICE_LAUNCH %s\n' "$(date)"
if [ -s "$PIDFILE" ];then
 OLD=$(cat "$PIDFILE" 2>/dev/null)
 if [[ "$OLD" =~ ^[0-9]+$ ]] && kill -0 "$OLD" 2>/dev/null;then
  CMD=$(tr '\0' ' ' < "/proc/$OLD/cmdline" 2>/dev/null)
  if [[ "$CMD" == *"homeassistant"* ]];then echo "HA_ALREADY_RUNNING_PID=$OLD";exit 0;fi
 fi
fi
if [ ! -x "$V/bin/python" ];then echo 'HA_VENV_MISSING';exit 2;fi
if [ ! -f "$P/lib/libc++_ha_termux30.so" ];then echo 'HA_CXX_RUNTIME_MISSING';exit 3;fi
# Handle Home Assistant's own graceful restart request (exit 100).
# Bound consecutive restart attempts so a persistent failure cannot thrash this phone.
ATTEMPTS=0
while true; do
  LD_PRELOAD="$P/lib/libc++_ha_termux30.so" "$V/bin/python" -m homeassistant \
    --config "$C" --ignore-os-check --skip-pip --log-rotate-days 7 &
  PID=$!
  echo "$PID" > "$PIDFILE"
  echo "HA_SPAWNED_PID=$PID $(date)"
  wait "$PID"
  RC=$?
  echo "HA_EXIT_RC=$RC $(date)"
  if [ "$RC" -eq 100 ] && [ "$ATTEMPTS" -lt 5 ]; then
    ATTEMPTS=$((ATTEMPTS+1))
    echo "HA_REQUESTED_RESTART_ATTEMPT=$ATTEMPTS"
    sleep 5
    continue
  fi
  if [ "$(cat "$PIDFILE" 2>/dev/null)" = "$PID" ];then rm -f "$PIDFILE";fi
  exit "$RC"
done
