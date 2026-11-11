# 04｜小米官方 Xiaomi Home v0.5.0 集成与 OAuth

官方来源：[XiaoMi/ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home) · 本案例稳定标签 **v0.5.0** · 源代码 commit `75b3acb6325a3a8d295688b13904737d6738a6a5`（按当前案例记录）。

## 1. 安装前提

完成 HA Core 启动，确保能访问 `http://127.0.0.1:8125/`，并且以下 Android Python 依赖已经可正常导入：

- `construct==2.10.70`
- `paho-mqtt==2.1.0`
- 项目依赖的 numpy、cryptography、psutil 及网络相关模块

安装**官方集成**，不使用网上来历不明的同名 fork。

## 2. 源代码准备

在电脑上从官方仓库取得 `v0.5.0`，确认对应 commit、`custom_components/xiaomi_home/manifest.json` 的 domain/version，按官方 README 的操作将自定义集成目录复制到：

`~/zuk-ha-native/config-ha/custom_components/xiaomi_home/`

原实机采用离线 tar + SHA256SUMS + Python wheel 验证后复制；本仓库不重新发布第三方源码或完整离线包。安装前不要覆盖已存在且完成 OAuth 的集成目录。

将所需的 Android 兼容依赖安装到 `venv-ha`，再运行 [`verify-xiaomi-home.sh`](../scripts/on-device/verify-xiaomi-home.sh) 检查 Python import。然后**仅重启原生 HA 8125**，不要误停其他旧实例。

## 3. 配置流程

HA → 设置 → 设备与服务 → 添加集成 → **Xiaomi Home**，选择自己实际使用的账号地区，再按小米授权提示登录。

- Android 浏览器中的 OAuth 回调可能被固定为 `homeassistant.local:8123`。在确认是自己发起的正规授权且确有本机重定向失败时，只调整回调 URL 的**域名和端口**为本机 HA 地址 `127.0.0.1:8125` 或同局域网地址；**不要更改路径和查询参数**。
- OAuth 回调 URL 含临时 `code`、`state` 等敏感参数，**绝对不要提交截图、链接或日志到公开仓库**。
- 小米授权成功后，某些手机浏览器无法执行网页的 `window.close()`；可手工关闭授权标签，回到原来的 HA 集成配置页继续。
- `already_in_progress` 常表示有另一配置流程尚未结束：关闭旧配置标签、只保留一个 OAuth 流程，必要时对**原生 HA**做一次正常重启（不要清缓存、不要删 `.storage`）。

## 4. 设备验证与在线问题

- 查看 HA 设备注册表、实体注册表和 UI；设备/实体注册成功不代表当前在线或所有属性可控制。
- 蓝牙/Mesh 设备的在线状态可能受网关、协议、网络分区影响，不能简单地把“灯离线”归咎于 Termux。
- 集成配置只在成功完成最后一步后保存，OAuth 页面显示“授权成功”并不自动等于实体已经导入。
- 设备名称、房间布局、云端 ID、设备 token 和 IP 属于私有信息，不写到公开文档。

## 5. 验收

至少确认：集成处于 loaded/已配置状态；若干安全设备的属性读数正确；有权限的控制项通过 UI 能正常变化；长时间离线设备应独立排查网关/设备供电。
