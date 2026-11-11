#!/usr/bin/env bash
# Deliberately non-destructive APK user update. No /system changes, no HA data touches.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "usage: ADB_SERIAL=YOUR_DEVICE_SERIAL $0 /path/to/Google-WebView119-API24-ARM64.apk" >&2; exit 2; }
: "${ADB_SERIAL:?Set ADB_SERIAL explicitly; inspect adb devices -l first}"
HERE=$(cd "$(dirname "$0")" && pwd)
"$HERE/verify-google-webview-119.sh" "$1"
SDK=$(adb -s "$ADB_SERIAL" shell getprop ro.build.version.sdk | tr -d '\r')
ABI=$(adb -s "$ADB_SERIAL" shell getprop ro.product.cpu.abi | tr -d '\r')
[[ "$SDK" == 24 && "$ABI" == arm64-v8a ]] || { echo "unexpected target sdk=$SDK abi=$ABI" >&2; exit 9; }
if [[ $(adb -s "$ADB_SERIAL" shell settings get global webview_provider | tr -d '\r') != com.google.android.webview ]]; then
  echo 'unexpected WebView provider — aborting' >&2; exit 10
fi
printf 'Installing verified WebView user update on %s (SDK %s, %s)\n' "$ADB_SERIAL" "$SDK" "$ABI"
adb -s "$ADB_SERIAL" install -r "$1"
echo '== Runtime package =='
adb -s "$ADB_SERIAL" shell pm path com.google.android.webview
adb -s "$ADB_SERIAL" shell dumpsys package com.google.android.webview | grep -m1 'versionName='
echo '== Read-only verification =='
adb -s "$ADB_SERIAL" shell settings get global webview_provider
# Do NOT clear HA data, force-stop unrelated packages, change Home launcher, or reboot.
echo 'Next: open HA Companion and confirm WebViewFactory version 119 in local filtered logcat.'
