#!/data/data/com.termux/files/usr/bin/bash
P=/data/data/com.termux/files/usr
H=/data/data/com.termux/files/home; L="$H/zuk-ha-native"
export PREFIX="$P" HOME="$H" PATH="$P/bin:/system/bin"
if [ -f "$L/run/ha-native.pid" ];then
 PID=$(cat "$L/run/ha-native.pid")
 if kill -0 "$PID" 2>/dev/null;then
  echo "PROCESS_RUNNING_PID=$PID"
 else echo "PIDFILE_STALE=$PID";fi
else echo 'NO_PIDFILE';fi
"$P/bin/curl" -m 3 -s -o /dev/null -w 'HTTP_8125=%{http_code}\n' http://127.0.0.1:8125/
"$P/bin/curl" -m 3 -s -o /dev/null -w 'HTTP_8124=%{http_code}\n' http://127.0.0.1:8124/
