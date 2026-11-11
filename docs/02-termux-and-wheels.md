# 02｜Termux Python 3.14 与 Android 原生依赖

> 这是端服一体方案的技术门槛。此处记录实机工程的**方法与环境**，不是承诺任意 Android 7 手机执行一条 `pip install homeassistant` 即可启动。若没有 Android wheel 构建能力，建议优先在树莓派或支持的 Linux 主机上运行 HA，旧手机仅作为控制屏。

## 1. Termux 签名与包管理

使用同一发行渠道签名的 Termux 与 Termux:Boot；不同渠道插件可能由于共享 UID/签名不一致而无法运行。实际验证环境：**Termux 0.117（F-Droid 签名）**、**Termux:Boot 0.8.1（F-Droid 签名）**。不要为了升级擅自卸载一个已经存放 HA 数据的 Termux！

```bash
# 在 Termux 内执行；不同镜像仓库可能提供不同包版本
pkg update
pkg install python git curl tar clang make pkg-config
python -V
uname -m
```

实机使用 Python **3.14.10**，不是多数 Debian/Linux HA Docker 镜像的 Python 版本。先验证 Python/ABI，后装依赖。

## 2. Android ARM64 wheels 的 ABI

- 目标 `cp314-cp314-android_24_arm64_v8a`，Android API 24，C library 为 **Bionic**。
- 不要把 `manylinux` / glibc / macOS wheel 改名为 Android wheel，`ELF` 依赖仍不匹配。
- 纯 Python 的 `py3-none-any` 可优先使用（但仍需验证依赖和行为）。
- `cryptography`、`orjson`、`cffi`、`PyNaCl`、`pillow`、`numpy`、`grpcio` 等可能涉及 Android ABI/系统库兼容；具体版本按 HA 2026.11.0 的版本约束来确定。
- 实机工程基于 **Mac M4 + Android NDK 27.3.13750724 (r27d) + cibuildwheel 3.3.0 + 真机导入检查**；并不代表任意原生库直接可用。

参考：[cibuildwheel Android 平台说明](https://cibuildwheel.pypa.io/en/stable/platforms/#android) · [Python wheel 平台标签规范](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#android)。

## 3. 分层适配流程

1. 在主机端从官方 PyPI/HA lock 采集所需依赖、版本和 SHA-256。
2. 分为 `py3-none-any`、已有 Android wheel、需要 NDK 编译的 C/C++、需要 Rust/maturin 编译的扩展。
3. 使用独立 Android NDK 和匹配的 CPython ABI 编译；审查 wheel 的 `WHEEL` 标签、`.so` 的 AArch64 ELF、动态依赖和构建后端。
4. 在目标 Termux Python 3.14 真机 `import` 验证，不仅依靠构建成功。
5. 导入成功后，再把轮子并入可审计的离线依赖清单。不要把编译缓存、含日志的构建目录直接公开。

```bash
# 示例：在目标 Termux 建立隔离环境
mkdir -p ~/zuk-ha-native
python -m venv ~/zuk-ha-native/venv-ha
~/zuk-ha-native/venv-ha/bin/python -V

# 示例：仅当你已经准备好 Android 兼容 wheel 时，才可以逐个离线安装
# uv pip install --offline --no-deps --python ~/zuk-ha-native/venv-ha/bin/python ./wheels/PACKAGE.whl
```

## 4. libc++ 动态库特殊适配

本案例服务管理脚本通过 `LD_PRELOAD=$PREFIX/lib/libc++_ha_termux30.so` 注入**实机另行构建/验收**的 Termux 兼容 C++ 运行库。仓库不分发该 `.so`；没有它，原服务脚本会明确报 `HA_CXX_RUNTIME_MISSING` 而非盲目启动。

**强烈不建议**下载匿名构建的 `.so` 覆盖系统 `libc++`；应独立验证系统 ABI 与链接符号，并保留原环境。原构建器工作区属于另一套实验（AndroidWheelForge），本仓库只提供复现思路及服务脚本。

## 5. 验收标准

```bash
~/zuk-ha-native/venv-ha/bin/python - <<'PY'
import sys, platform
print(sys.version)
print(platform.machine())
PY
```

检查 HA 必需模块的版本及 `import`，记录失败模块和 Android 特有 linker 信息。依赖阶段未成功，不应进入 HA 正式启动步骤。
