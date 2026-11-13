#!/usr/bin/env bash
# Requires Android NDK r30 (or a compatible toolchain) and sherpa-onnx v2.0.1 shared Termux bundle.
set -euo pipefail
: "${ANDROID_NDK_HOME:?Set ANDROID_NDK_HOME to a verified Android NDK installation}"
: "${SHERPA_ONNX_HOME:?Set SHERPA_ONNX_HOME to sherpa-onnx-v2.0.1-android-aarch64-termux-shared}"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
CC="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android24-clang"
[[ -x "$CC" ]] || { echo 'NDK clang for macOS not found; adapt toolchain host path for Linux' >&2; exit 1; }
[[ -f "$SHERPA_ONNX_HOME/include/sherpa-onnx/c-api/c-api.h" ]] || { echo 'missing sherpa-onnx C API header' >&2; exit 2; }
mkdir -p "$SCRIPT_DIR/local-bin"
"$CC" -fPIC -shared -O2 -Wall -Wextra -Werror \
  -I"$SHERPA_ONNX_HOME/include" "$SCRIPT_DIR/sensevoice_bridge.c" \
  -L"$SHERPA_ONNX_HOME/lib" -lsherpa-onnx-c-api \
  -o "$SCRIPT_DIR/local-bin/libzuk-sensevoice.so"
for p in libsherpa-onnx-c-api.so libonnxruntime.so; do
  cp "$SHERPA_ONNX_HOME/lib/$p" "$SCRIPT_DIR/local-bin/$p"
done
cp "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/darwin-x86_64/sysroot/usr/lib/aarch64-linux-android/libc++_shared.so" \
  "$SCRIPT_DIR/local-bin/libc++_shared.so"
echo 'Native ARM64 bridge built. Distribute only to your own device; never commit local-bin/.'
