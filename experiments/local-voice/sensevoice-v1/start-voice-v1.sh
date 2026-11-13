#!/data/data/com.termux/files/usr/bin/bash
# Termux app process only. No direct root and no modifications to HA/OS.
set -u
D=/data/data/com.termux/files/home/zuk-ha-voice-v1
P=/data/data/com.termux/files/usr
export PREFIX="$P" HOME=/data/data/com.termux/files/home PATH="$P/bin:/system/bin" LD_LIBRARY_PATH="$D/lib" TMPDIR="$P/tmp"
unset LD_PRELOAD
cd "$D" || exit 1
exec >> "$D/voice-v1.log" 2>&1
printf 'VOICE_V1_LAUNCH %s\n' "$(date)"
if "$P/bin/curl" -fsS --max-time 2 http://127.0.0.1:8127/health >/dev/null 2>&1;then
    echo 'VOICE_V1_ALREADY_RUNNING'
    exit 0
fi
exec "$P/bin/python3" "$D/server.py"
