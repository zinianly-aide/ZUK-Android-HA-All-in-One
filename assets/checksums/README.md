# 源码 / APK 素材索引与校验清单

**仓库只记录下载入口、实机验证版本、文件 SHA-256 与证书指纹，不提供第三方二进制文件，也不保存时效性 Cloudflare R2 签名直链。**

| 用途 | 来源 | 文件 / 版本 | 本次实机完整文件 SHA-256 |
|---|---|---|---|
| HA Android Minimal | [home-assistant/android 官方 Release](https://github.com/home-assistant/android/releases/tag/2026.11.1) | `app-minimal-release.apk` v2026.11.1，大小 55,052,939 B | `28abf486cd489ae796c3b4072b2af42b3efdfd149cf82643e92f5ff7656e0215` |
| Chrome 浏览器 | [APKMirror Chrome 119 版本页](https://www.apkmirror.com/apk/google-inc/chrome/chrome-119-0-6045-194-release/) | `com.android.chrome` v119.0.6045.194 / 604519421 / minAPI24 / ARM64，244,362,316 B | `a1df6a06ae9e6a7cdd1b0b22b38b98214f105fbe0755893189d239e45a37b3e7` |
| Android System WebView | [APKMirror WebView 119 版本页](https://www.apkmirror.com/apk/google-inc/android-system-webview/android-system-webview-119-0-6045-194-release/) | `com.google.android.webview` v119.0.6045.194 / 604519401 / minAPI24 / ARM64，209,283,597 B | `940fb37a9d91d42ceacbde4c076e30eb2683c35d5901b95438d540337cd2df2b` |
| Termux:Boot (F-Droid) | [F-Droid 官方 repo](https://f-droid.org/packages/com.termux.boot/) | `com.termux.boot_1000.apk` v0.8.1 | `6f7cf9b94f539d3efd4af3544ff819947b49395275d8cfa7e5f80de14f3d9cf8` |
| Xiaomi Home | [XiaoMi/ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home/releases/tag/v0.5.0) | 版本 v0.5.0 / commit `75b3acb6325a3a8d295688b13904737d6738a6a5` | 请核对上游发布的 commit/tag/文件清单；不包含在本项目的 APK 哈希中 |

## 签名证书（实机核对）

| 二进制 | APK signer SHA-256 |
|---|---|
| HA Android Minimal v2026.11.1 | `11194ba809b42ddf0e1a7dec6842a59c7ff1119c5482e95febffd5c6014daa5a`（O=Home Assistant） |
| Chrome 119 | `f0fd6c5b410f25cb25c3b53346c8972fae30f8ee7411df910480ad6b2d60db83`（O=Google Inc.） |
| WebView 119 | `6faf3c4140407473400934d117815a21af1cfefc5c0bee61c858bc3d72ba6fe5`（O=Google Inc., CN=webview；和原 WebView 55 证书相同） |
| Termux:Boot 0.8.1 F-Droid | `228fb2cfe90831c1499ec3ccaf61e96e8e1ce70766b9474672ce427334d41c42`（与已有 Termux 0.117 F-Droid 签名相同） |

## 本机验证

```bash
shasum -a 256 /path/to/downloaded.apk
# Android SDK Build Tools 提供 aapt 和 apksigner
aapt dump badging /path/to/downloaded.apk
apksigner verify --verbose --print-certs /path/to/downloaded.apk
```

上述哈希适用于本次核验过的**特定构建文件**，不代表相同版本的不同 DPI/ABI 包或 Bundle 都相同。若哈希不匹配，先核对来源、版本、变体和文件完整性，**不要绕过验证直接安装**。

**来源声明：** APKMirror 是第三方下载索引，不是 Google 官方托管。请先核对包名、Android API、完整 SHA-256 和 Google 签名，不把外部链接的存在当成真实性保证。Android 7 和 Chromium 119 都已停止安全更新。
