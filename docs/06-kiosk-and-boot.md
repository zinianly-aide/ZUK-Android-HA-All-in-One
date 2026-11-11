# 06｜端服一体的开机启动、控制屏与长稳运维

## A. Termux:Boot（服务端）

1. 安装**与当前 Termux 相同签名发行渠道**的 Termux:Boot；本实机为 F-Droid Termux 0.117 + F-Droid Termux:Boot 0.8.1。
2. 手工打开一次 Termux:Boot App 以启用对应 Android 开机广播接收器。不要以为仅安装 APK 就一定生效。
3. 在 Termux 中创建 `~/.termux/boot`，复制 [`10-start-zuk-ha-core`](../scripts/on-device/10-start-zuk-ha-core) 到该目录，`chmod 700`，确保文件归 Termux 应用用户而非 root 所有。
4. 脚本先检查 PID 及进程名，若已有 HA 则退出；否则延迟 20 秒后启动 `~/zuk-ha-native/ha-native-service.sh`。
5. 先做**不重启**的脚本幂等测试：运行两次，检查 `logs/termux-boot-ha.log` 中的 `BOOT_HA_ALREADY_RUNNING_PID`，服务仍只有一个 PID。
6. 在已经备份、手机可恢复的情况下，进行**实际重启**验收；本实机截至文档编写时不宣称已完成该项。

## B. 手机控制端（前台）

- 首选已通过登录验收的 Home Assistant Companion；或 Chrome“添加到主屏幕”入口。
- 在 HA 新建**专用仪表盘**：上方显示房间/时间/网络状态，中部大按钮控制灯、窗帘、空调，底部显示传感器和离线设备。
- 保留系统 Home 键和 ZUI 桌面入口，连续稳定运行且有退出方式后才考虑专用启动器或 Kiosk 锁定。仅在本机触摸和实体控制均通过测试后设置自动启动前台 UI。
- 没有 Google Play 服务、Android 7 系统老旧时，Chrome 桌面入口未必支持真正的 WebAPK/PWA 独立无地址栏。

## C. 省电与稳定性

- 检查 ZUI 自启动限制、Termux 后台权限、Wi-Fi 休眠策略、电池优化；优先通过系统设置逐项评估，不建议直接关闭 Android 安全机制。
- HA 数据写入需要稳定存储；低存储量时优先减少日志、Recorder 保留期和大附件，**先备份后清理**。
- 长期供电建议使用质量可靠的充电配件、保留空气流通，关注电池温度与健康。老旧锂电池鼓包/异常高温应停用检修，不应密封在 3D 打印外壳内长期充电。
- 对离线 Mesh 设备，区分米家云状态与 HA 实体状态，不要通过反复删除 OAuth 账号解决。

## D. 验收清单

参见 [09｜实机验收](09-validation.md)。服务端重启成功 **不等于** 前台 App 自动恢复登录状态；需要分别验证。
