# 03｜原生 Home Assistant Core 2026.11.0 与进程管理

## 前提

- 已完成 [02｜Android 兼容 Python 依赖](02-termux-and-wheels.md) 的所有 wheel 验收。
- 已在 `~/zuk-ha-native/venv-ha` 安装 **Home Assistant Core 2026.11.0** 与其对应依赖；本步骤不会自动下载或构建它们。
- 已将工程中验证过的 Termux C++ 兼容库放在 `$PREFIX/lib/libc++_ha_termux30.so`（无该文件不能使用当前实机服务脚本）。
- 无其他服务占用 `8125`，本机历史 HA 如在 `8124` 可并存。

## 1. 独立配置目录

```bash
mkdir -p ~/zuk-ha-native/{config-ha,logs,run}
cat > ~/zuk-ha-native/config-ha/configuration.yaml <<'YAML'
homeassistant:
  name: Android HA Lab
http:
  server_port: 8125
config:
frontend:
YAML
```

注意：这是一个最小配置**模板**，实际部署可由 HA 首次引导补充其他文件；不应覆盖已有配置。若已部署过，先备份再修改。

## 2. 安装本仓库脚本

以下命令在 **Termux** 执行；脚本需先通过可靠传输方式放到本机目录（如 Mac ADB `push` 至用户可访问位置，再由 Termux 复制）：

```bash
cp ha-native-service.sh ~/zuk-ha-native/ha-native-service.sh
cp ha-native-stop.sh ~/zuk-ha-native/ha-native-stop.sh
cp ha-native-status.sh ~/zuk-ha-native/ha-native-status.sh
chmod 700 ~/zuk-ha-native/ha-native-*.sh
```

真实可用脚本位于 [`scripts/on-device`](../scripts/on-device/)，与本案例运行的进程管理设计一致。脚本是**有前提的启动器**，不是 HA Core 安装器。

## 3. 启动与验证

```bash
bash ~/zuk-ha-native/ha-native-service.sh
# 在另一个 Termux session 执行（服务脚本常驻前台）
bash ~/zuk-ha-native/ha-native-status.sh
curl -I http://127.0.0.1:8125/
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8125/api/
```

正常表现：`/` 为 HTTP **200**；无认证访问 `/api/` 返回 **401** 属于预期行为。不要把 401 误判为 Core 未启动。

> 脚本通过 `--ignore-os-check --skip-pip` 来支持当前不受官方支持的 Termux 运行环境；**这绕过了官方环境检查/自动依赖安装，因此不能放松先前的 wheel 兼容验证**。

## 4. 运行控制与回滚

- 运行进程 PID 写入 `~/zuk-ha-native/run/ha-native.pid`。
- 再次运行服务脚本会检查 PID 和命令行，尽量避免启动第二份 HA。
- 结束服务：`bash ~/zuk-ha-native/ha-native-stop.sh`。首次关闭可能需要等待写盘完成。
- 日志在 `~/zuk-ha-native/logs/`；**日志可能包含 OAuth 回调参数，不要直接贴到公开 Issue**。
- HA 的正常软件重启退出码 100 会由脚本有限次数拉起；其他失败不会无限重启。
- 若无法启动，先检查兼容库、Python 模块导入、文件权限、空间和端口，不要删除 `config-ha`。

## 5. 多实例边界

原生 HA 和旧 Debian/容器 HA 可能同时存在；请按不同端口、Python 环境、配置目录分别管理。严禁把另一个实例正在使用的 `.storage` 直接复制过来后并发写入。
