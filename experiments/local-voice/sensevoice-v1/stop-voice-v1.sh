#!/data/data/com.termux/files/usr/bin/bash
# Safe stop only exact SenseVoice V1 service; never kill other Python/HA processes.
set -euo pipefail
D=/data/data/com.termux/files/home/zuk-ha-voice-v1
count=0
for proc in /proc/[0-9]*/cmdline; do
  [[ -r "$proc" ]] || continue
  cmd=$(tr '\0' ' ' < "$proc" 2>/dev/null || true)
  [[ "$cmd" == *"$D/server.py"* ]] || continue
  pid=${proc#/proc/};pid=${pid%/cmdline}
  [[ "$pid" =~ ^[0-9]+$ ]] || continue
  echo "Stopping exact V1 service PID=$pid"
  kill -TERM "$pid"
  ((count+=1))
done
if ((count==0)); then echo 'SenseVoice V1 not running'; fi
