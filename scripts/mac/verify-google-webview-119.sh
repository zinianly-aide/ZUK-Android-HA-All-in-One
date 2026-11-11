#!/usr/bin/env bash
# Offline APK verification. Never install an unverified binary.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "usage: $0 /path/to/Google-WebView119-API24-ARM64.apk" >&2; exit 2; }
APK="$1"
[[ -f "$APK" ]] || { echo 'APK not found' >&2; exit 2; }
EXPECTED_SHA='940fb37a9d91d42ceacbde4c076e30eb2683c35d5901b95438d540337cd2df2b'
EXPECTED_CERT='6faf3c4140407473400934d117815a21af1cfefc5c0bee61c858bc3d72ba6fe5'
command -v shasum >/dev/null && command -v aapt >/dev/null && command -v apksigner >/dev/null || { echo 'requires shasum, aapt and apksigner on PATH' >&2; exit 2; }
ACTUAL_SHA=$(shasum -a 256 "$APK" | awk '{print tolower($1)}')
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || { echo 'SHA256 mismatch; wrong variant or corrupted download' >&2; exit 3; }
CERTS=$(apksigner verify --print-certs "$APK") || { echo 'APK signature verification failed' >&2; exit 4; }
CERT=$(awk -F': ' '/Signer #1 certificate SHA-256 digest:/ {print tolower($2);exit}' <<< "$CERTS")
[[ "$CERT" == "$EXPECTED_CERT" ]] || { echo 'Google WebView signing certificate mismatch' >&2; exit 5; }
META=$(aapt dump badging "$APK")
grep -q "^package: name='com.google.android.webview' versionCode='604519401' versionName='119.0.6045.194'" <<< "$META" || { echo 'wrong APK package or version' >&2; exit 6; }
grep -q "^sdkVersion:'24'" <<< "$META" || { echo 'wrong minimum Android API' >&2; exit 7; }
grep -q "^native-code:.*'arm64-v8a'" <<< "$META" || { echo 'missing ARM64 native library' >&2; exit 8; }
printf 'VERIFIED WebView 119.0.6045.194 SHA256=%s certificate=%s\n' "$ACTUAL_SHA" "$CERT"
