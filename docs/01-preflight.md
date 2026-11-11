# 01｜环境检查、备份与安全基线

## 1. 设备检查（Mac / Linux ADB 主机）

确保手机已经开启开发者选项与 USB 调试，手机上确认 ADB 授权。**多设备连接必须显式指定序列号**，以免误操作电视或其他 Android 设备：

```bash
adb devices -l
export ADB_SERIAL=YOUR_DEVICE_SERIAL
adb -s "$ADB_SERIAL" shell getprop ro.product.model
adb -s "$ADB_SERIAL" shell getprop ro.build.version.sdk
adb -s "$ADB_SERIAL" shell getprop ro.product.cpu.abi
adb -s "$ADB_SERIAL" shell uname -a
adb -s "$ADB_SERIAL" shell df -h /data
```

经验证的参考环境为 ZUK Z2121、Android API 24、`arm64-v8a`、Kernel 3.18.31；这不是可通用刷入的内核包。

## 2. 备份

- 先在 Termux 中**停止原生 HA**，使其配置和数据库进入一致状态：`bash ~/zuk-ha-native/ha-native-stop.sh`；若有其他 HA 实例，**不要停错服务**。
- 对 `~/zuk-ha-native/config-ha/`、自定义集成、Python 版本、依赖清单及自建脚本进行本地备份。备份存放在可信电脑/加密磁盘，切勿上传公开 GitHub。
- 如计划升级 ROM/Boot/Recovery，需要额外具备可靠的系统分区备份与恢复方案。仅更新普通 WebView 应用时，不要动 Boot/System 分区。
- 确认至少数 GB 可用磁盘空间用于 Chrome/WebView 安装、dex 优化、日志和 HA 数据库；不要在设备存储紧张时尝试批量升级。

## 3. 基础安全

- 只对可信局域网开放 HA 服务，不直接做公网端口转发。
- HA 创建单独管理账户和可靠密码；设备端使用最小权限用户。不要把管理员 access token 放进 shell 脚本或 GitHub Actions Secrets 之外的任何公开文件。
- 使用 USB 供电、避免手机过热或鼓包；老旧电池不适合在封闭壳中长期满电充电。
- 保留可用的原 Android 桌面、Termux 和 Chrome，在 HA Companion 未通过验收前**不要启用单应用锁定模式**。

下一步：[02｜Termux 与 Android wheels](02-termux-and-wheels.md)。
