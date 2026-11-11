# 05｜官方 Android 客户端、WebView 119 与 Chrome PWA

## 背景：为什么 Android 7 出现白屏

ZUK Android 7 出厂 `com.google.android.webview 55.0.2883.91`。安装官方 HA Android Companion `2026.11.1-minimal` 后，白色启动页可能无法进入授权界面。实机 ADB 日志出现：

```text
HAWebViewKt: Webview started
Uncaught SyntaxError: Unexpected token import
```

服务端仍为 HTTP 200，故障位于 **系统 WebView 的现代 JS 兼容性**，不是 Home Assistant Core 或米家数据问题。

## 1. 下载官方 HA Android Minimal

- 官方发行页：[home-assistant/android 2026.11.1](https://github.com/home-assistant/android/releases/tag/2026.11.1)
- 选择 `app-minimal-release.apk`。Minimal 版不需要完整 Google Play 服务（与非 Minimal 包名不同），实机安装为 `io.homeassistant.companion.android.minimal`。
- 实机核验 SHA-256 见 [二进制记录](../assets/checksums/README.md)。
- 对 ZUK 指定 ADB 设备，避免连接到投影仪时误安装：

```bash
export ADB_SERIAL=YOUR_DEVICE_SERIAL
adb -s "$ADB_SERIAL" install -r app-minimal-release.apk
adb -s "$ADB_SERIAL" shell am start -n \
  io.homeassistant.companion.android.minimal/io.homeassistant.companion.android.launch.LaunchActivity
```

## 2. WebView 119 官方签名更新（Android 7）

ZUK ZUI 固件在 `res/xml/config_webview_packages.xml` 里**只允许 `com.google.android.webview`**。安装 `com.android.chrome` **不会自动替换 WebView**；命令显示的偏好值也不一定代表实际加载引擎。必须用 Google 签名、同包名的 WebView 更新应用。

- 适配版本：`com.google.android.webview` `119.0.6045.194`（`604519401`），`minAPI24`、`arm64-v8a`。
- 从可信发布页面获取原始 APK、在 Mac 上进行 ZIP/v2+v3 签名、SHA-256、包名、SDK/ABI 和 Google 证书指纹验证；见本仓库 [校验记录](../assets/checksums/README.md)。
- **不要**从不明网盘取得修改版 WebView，也不要用投影仪的厂家签名 WebView 覆盖 ZUK。
- 确认 `/system/app` 原始 WebView 55 可回退后，常规更新即可：

```bash
export ADB_SERIAL=YOUR_DEVICE_SERIAL
adb -s "$ADB_SERIAL" install -r \
  com.google.android.webview_119.0.6045.194-604519401_minAPI24_arm64-v8a.apk
adb -s "$ADB_SERIAL" shell pm path com.google.android.webview
adb -s "$ADB_SERIAL" shell settings get global webview_provider
```

**注意：** 上面的 APK 文件名只是重命名示例，应使用你**实际下载且已核验**的文件路径；不在仓库分发二进制文件。正常安装到 `/data/app/.../base.apk`，保留原 `/system/app/WebViewGoogle/...` 文件。

本案例升级后 ADB 确认：

```text
WebViewFactory: Loading com.google.android.webview version 119.0.6045.194
```

WebView 119 在 Android 7 可能出现 `android.webkit.PacProcessor` 类缺失警告（已知兼容日志）；不应只凭这条日志判定失败，以**能否显示 HA 登录 UI、进程状态、崩溃日志**综合判断。实机已看到正常的“你的 Home Assistant 地址？”输入页面；尚需验证完整账号登录和所有控制操作。

## 3. 客户端连接本机 HA

```text
http://127.0.0.1:8125
```

使用 HA 用户名与密码登录。Chrome 中的登录信息**不会自动共享到** Android Companion。若需要用其他局域网手机访问，使用 `http://<ZUK_LAN_IP>:8125/`。

## 4. Chrome 119 作为替代控制入口

Chrome 119 是最后一代兼容 Android 7 的 Chrome。独立浏览器实机可以访问/登录本机 HA。即便系统 WebView 仍是旧版，Chrome 本身也可正常浏览 HA；它们是不同的渲染路径。

- 在 Chrome 打开本机 HA，右上角菜单 → **添加到主屏幕** / **安装应用**（如果存在）；创建快捷入口。
- HA `manifest.json` 实测 `display: standalone`、`start_url: /?homescreen=1`；是否真正独立无地址栏仍取决于 Chrome、系统限制和安装方式。
- 此机无 Google Play 服务，PWA 安装可能退化为普通浏览器快捷方式，不保证与完整原生 Companion 功能相同。

## 5. 实际控制能力差别

| 能力 | Chrome / PWA | Android Companion |
|---|---|---|
| HA Dashboard、实体控制 | 是 | 是 |
| 可单独添加桌面入口 | 通常可以 | 是 |
| 手机原生传感器、原生通知 | 有限制 | 支持更多（依权限/版本） |
| 系统 WebView 依赖 | 否（Chrome 自己渲染） | 是 |
| 需要登录 HA | 是 | 是（登录状态不共享） |

**不要因为安装了 Chrome 119 就盲目将 `webview_provider` 写成 `com.android.chrome`**。本机 ZUI XML 配置不允许它，实际切换会失败。也不建议修改 framework-res 或直接替换 `/system` 来绕过限制。
