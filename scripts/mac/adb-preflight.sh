#!/usr/bin/env bash
# Read-only: preflight for ZUK-like Android HA all-in-one setup.
set -euo pipefail
: "${ADB_SERIAL:?Set ADB_SERIAL explicitly (adb devices -l first); never assume first device}"
command -v adb >/dev/null || { echo 'adb not found' >&2; exit 2; }
run() { adb -s "$ADB_SERIAL" "$@"; }
echo '== ADB device =='
run get-state
run shell getprop ro.product.model
run shell getprop ro.build.version.sdk
run shell getprop ro.product.cpu.abi
run shell uname -a
run shell df -h /data
echo '== Existing packages =='
run shell pm list packages | grep -E 'com.termux|homeassistant|android.chrome|google.android.webview' || true
echo '== WebView provider =='
run shell settings get global webview_provider
run shell pm path com.google.android.webview || true
echo '== HA service status on device (unauthenticated) =='
run shell 'if command -v curl >/dev/null; then curl -sS -m 3 -o /dev/null -w "HTTP_8125=%{http_code}\n" http://127.0.0.1:8125/; else echo "curl unavailable in android shell"; fi' || true
