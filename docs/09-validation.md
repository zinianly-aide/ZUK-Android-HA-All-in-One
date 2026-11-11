# 09｜验收矩阵（实测 vs. 待验证）

本矩阵按实际 ZUK Z2 Pro 的 2026-11-12 检查记录整理；“已验证”仅代表对应观察项，不暗示长稳、断电恢复、全部米家设备均通过。

| 验收项 | 状态 | 可复核证据/方法 |
|---|---|---|
| ZUK Z2121 Android 7 / ARM64 / Kernel 3.18 | 已确认 | `adb getprop` / `uname -a` |
| Termux CPython 3.14.10 + Android wheel | 部分包已验证 | Native wheel 标签/ELF + 真机 import；完整编译配方未随仓库发布 |
| HA Core 2026.11.0，`8125` HTTP 200 | 已验证 | HTTP HEAD/GET，启动日志与 PID |
| 旧 HA 示例 `8124` 不被覆盖 | 已验证 | 原有实例端口独立 HTTP 响应 |
| Xiaomi Home v0.5.0 集成注册 | 已验证 | 本机 HA 配置/设备/实体注册；不公开私有设备清单 |
| 多台米家设备长期可靠控制 | **待完整验收** | 房间逐台操作、网关状态、在线率 |
| 官方 Companion 2026.11.1 Minimal 安装 | 已验证 | `adb install`、包版本 |
| Chrome 119 可浏览本机 HA | 已验证 | Chrome 真实登录使用 |
| Google WebView 119 Google 签名匹配 | 已验证 | SHA256/APK v2+v3 证书 + ZUK 原始 WebView cert |
| Companion 加载 WebView 119 | 已验证 | `WebViewFactory: Loading ... version 119...` |
| Companion 从白屏进入服务器地址界面 | 已验证 | Android UI 树出现“你的 Home Assistant 地址？” |
| Companion 完成账户登录与设备操作 | **待验证** | 真实登录/实体控制 |
| Termux:Boot 已安装且幂等脚本检查通过 | 已验证（非重启） | PID 检测、重复启动不创建第二个 HA |
| 真正重启后自动恢复 + 72h 稳定 | **待验证** | 需重启及长稳测试 |
| 全屏 Kiosk/默认桌面替换 | **未启用** | 目前保留 ZUI 原桌面，避免锁定设备 |

## 验收步骤建议

1. 建立配置的私有备份（不要上传此公开仓库）。
2. ZUK 客户端连接 `http://127.0.0.1:8125`，人工登录并记录成功/失败结果。
3. 在安全可控条件下仅对普通灯/窗帘等低风险设备做非危险的开关/读取测试。
4. 验证锁屏、亮屏、Wi-Fi 断开重连、后台驻留与重启恢复。
5. 记录 CPU、内存、HA Recorder 增长和设备温度，故障时只分享脱敏日志摘要。
