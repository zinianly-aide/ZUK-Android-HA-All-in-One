# 00｜项目概述与部署边界

**目标：** 旧手机一机三用：后台 HA Core 服务端、前台触控/语音入口、Home Assistant / Xiaomi Home 设备整合。与普通在 Android 上用浏览器访问 *其他* HA 服务不同，本项目将 HA 服务和控制端放在同一部 Android 设备上。

## 实际项目验证边界

- 已验证 Android 7.0 ARM64 ZUK Z2 Pro 可通过 Termux Python 3.14.10 + Android 兼容依赖启动 HA Core 2026.11.0。
- 已验证服务在 `127.0.0.1:8125` / 局域网可访问；手动脚本与进程运行状态核对通过；未宣称完成断电/重启长稳压力测试。
- 已验证官方 Xiaomi Home v0.5.0 正式创建集成与设备/实体注册；实际可控制性由网关和设备在线状态决定。
- 已验证 HA Android Minimal 客户端安装、WebView 119 能被 Android WebViewFactory 加载，旧 WebView 55 的 `Unexpected token import` 不再是当前阻塞；实际登录与仪表盘还需用户验收。
- 不承诺所有 HA 集成、全部硬件传感器、全部小米 MIoT API 或设备本地化在 Android 7 可用。

## 数据与端口隔离

```text
Termux HOME/
  zuk-ha-native/
    venv-ha/           # 原生 Python venv
    config-ha/         # 敏感的 HA 配置、用户、token、集成缓存：绝对不要公开
    logs/              # 运行日志，可能包含敏感 URL：不要公开
    run/ha-native.pid  # HA Core 进程 ID
    ha-native-service.sh
    ha-native-stop.sh
    ha-native-status.sh
  .termux/boot/
    10-start-zuk-ha-core
```

默认示例：原生 Core 在 `8125`，如设备另有历史 Debian HA 则保持其 `8124` 不变；**不要直接复用对方的 `config-ha` 或重写已有数据目录**。

## 推荐里程碑

| 里程碑 | 验收标准 |
|---|---|
| M0 Android/Termux 基础 | ADB 稳定、可执行 `python -V`、空间足够 |
| M1 Android wheel | 轮子架构正确、真机 import 成功 |
| M2 HA Core | 页面 200、API 401(未认证正常)、仅一个进程 |
| M3 Xiaomi Home | 官方 v0.5.0 初始化、OAuth、设备与实体可见 |
| M4 安卓前端 | Chrome 或 Companion 显示登录页、可登录、操作成功 |
| M5 运维 | 开机恢复、Wi-Fi 重连、异常重启与电池温度监控 |

## 定义

“端服一体”不等于关闭安全：同机 App 可访问 `127.0.0.1`，而通过局域网访问的其他设备仍须 HA 账户认证。服务端与客户端是**两个进程/组件**，故障定位应分开。
