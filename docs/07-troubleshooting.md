# 07｜故障排查与回滚

## 1. Companion 白色 HA Logo、无登录页

**症状：** Android App 白色启动画面；服务端 `8125` HTTP 200。检查 `adb logcat` 若出现 `Uncaught SyntaxError: Unexpected token import`，首先考虑 **旧 WebView 55** 不支持 HA 2026.11 前端语法。按 [05](05-android-client-webview.md) 验证同包名 Google WebView 119。

**重点看真正加载的引擎**：`WebViewFactory: Loading ... version 119...`。`settings get global webview_provider` 只是配置值，不能代替加载日志与 UI 验收。

## 2. 只装 Chrome 119，HA Companion 仍白屏

ZUK ZUI `config_webview_packages.xml` 仅允许 `com.google.android.webview`。`cmd webviewupdate set-webview-implementation com.android.chrome` 会失败。Chrome 本身可以浏览 HA，但**不会自动改变 Companion 使用的系统 WebView**。

## 3. WebView 119 的 PacProcessor 类警告

在 Android 7 可能出现 `java.lang.NoClassDefFoundError: android/webkit/PacProcessor`。若同时有 WebViewFactory 119 加载、客户端进程存活和正常的服务器输入页面，先把它作为**需观察的兼容警告**，不要直接删除 HA 数据；若有 Fatal Exception 则进一步隔离排查。

## 4. `already_in_progress`（Xiaomi Home）

- 同一账号/地区存在未结束的配置向导时会触发。
- 关闭重复浏览器标签，只保留一套新的授权流程。
- 核实 `.storage/core.config_entries` 里是否已经正式建成对应集成（仅在本机检查，不要公开该文件）。
- 仍失败时，仅对原生 HA 做正常停止/启动，再重新发起授权；**不应删除认证缓存或覆盖集成配置**。

## 5. HA 服务异常 / 旧 8124 受影响

- `bash ~/zuk-ha-native/ha-native-status.sh`。
- 对比 `/` HTTP 200、`/api/` 未认证 401、`pidfile` 进程号与命令行。
- 检查 Android venv 的 native `.so`、`LD_PRELOAD` 兼容库、文件权限、存储剩余空间。
- 核实是否无意占用旧实例 `8124`；本案例原生 HA 应只使用 `8125`。

## 6. WebView 更新导致其他应用异常

原版 ZUK WebView 55 位于 `/system/app/WebViewGoogle`，正常的同签名版本更新位于 `/data/app/com.google.android.webview-*`。优先从系统设置 → 应用 → Android System WebView → **卸载更新** 回到系统版本（菜单名称可能因 ROM 不同而变化）；如系统不支持或必须动用 root，先离线备份并评估风险，**不要先删系统 APK**。

## 7. 最小诊断命令

```bash
export ADB_SERIAL=YOUR_DEVICE_SERIAL
adb -s "$ADB_SERIAL" shell getprop ro.build.version.sdk
adb -s "$ADB_SERIAL" shell pm path com.google.android.webview
adb -s "$ADB_SERIAL" shell dumpsys package com.google.android.webview | grep versionName
adb -s "$ADB_SERIAL" shell settings get global webview_provider
adb -s "$ADB_SERIAL" shell dumpsys activity activities | grep mFocusedActivity
adb -s "$ADB_SERIAL" shell dumpsys power | grep mWakefulness
adb -s "$ADB_SERIAL" shell logcat -d -t 2000 | grep -E 'WebViewFactory|Uncaught SyntaxError|FATAL EXCEPTION'
```

**脱敏：** 在 GitHub Issue 共享前，务必移除 OAuth 回调 URL、token、家庭地址、手机号、用户 ID、设备 ID、局域网 IP 及任何明文账号。
