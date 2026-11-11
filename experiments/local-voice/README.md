# ZUK 离线中文语音实验（M0）

> 目标：在同一台 Android 7 / Termux 手机上完成 **Chrome 按钮录音 → 16 kHz PCM → Vosk ARM64 离线中文识别 → 指令匹配**。本版本严格为 **dry-run**：不会调用 Home Assistant API、不会执行设备动作、不会上传音频。服务只监听 `127.0.0.1:8126`。

## 实际验证（2026-11-12）

- ZUK Z2 Pro (`Z2121`)，Android 7，Termux Python 3.14.10，内存约 5.6 GiB。
- 直接从 Vosk Android AAR 0.3.47 提取 `jni/arm64-v8a/libvosk.so`，Python 标准库 `ctypes` 加载成功，无需重新编译 Vosk 或安装 Python Vosk wheel。
- `vosk-model-small-cn-0.22` 模型在 ZUK 上成功加载，初始化约 **0.98 秒**。
- 浏览器本地 HTML/JavaScript 已打开并显示 **“就绪”**、麦克风按钮。
- **离线推理验证：** 用 Mac 中文系统语音生成测试音频，16 kHz 单声道 PCM 输入 ZUK，返回“打开 客厅 灯”、匹配目标“客厅灯”，耗时约 **4.44 秒**。
- **待验证：** 用户真实麦克风录音识别准确率、持续录音稳定性；没有执行实际家电控制。

**追加实测报告：** [投影仪极光 AiAgent、SenseVoice INT8 与 Vosk 的 ZUK 同机对照](sensevoice-vs-projector-aiagent-2026-11-12.md)。

## 二进制来源与核验

不要把下载的 AAR / 模型放进 Git 仓库，它们属于上游发布内容。

| 内容 | 上游 URL | 本次 SHA-256 |
|---|---|---|
| Android Vosk runtime AAR 0.3.47 | `https://repo.maven.apache.org/maven2/com/alphacephei/vosk-android/0.3.47/vosk-android-0.3.47.aar` | `e3b82bb877753569f5e5f007807e4bc6165c34ba04e772d1df93552af0d27ffa` |
| 中文小模型 | `https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip` | `3af8b0e7e0f835ae9d414ce5df580237a3cfb08d586c9fbbb0f7ff29ad5b14ba` |

模型压缩包约 42 MB，解压约 65 MB；JNI AAR 的 ARM64 `libvosk.so` 约 8.5 MB。模型遵循 Vosk 官方列出的上游许可，项目不重新打包发布其文件。

## 复现（在 ZUK 的 Termux 应用里，不要通过 su 切换 UID 执行服务）

准备好文件后，确保目录为 Termux 用户所有，并且拥有正常的 Android app SELinux 标签：

```bash
mkdir -p ~/zuk-ha-voice-lab-m0/model ~/zuk-ha-voice-lab-m0/web
# 将本仓库 server.py、web/index.html、web/app.js 复制到相应路径。
# 将 vosk-model-small-cn-0.22.zip 放在 ~/zuk-ha-voice-lab-m0/。
# 将 vosk-android-0.3.47.aar 放在 ~/zuk-ha-voice-lab-m0/。
cd ~/zuk-ha-voice-lab-m0
python3 -m zipfile -e vosk-model-small-cn-0.22.zip model
unzip -p vosk-android-0.3.47.aar jni/arm64-v8a/libvosk.so > libvosk.so
python3 server.py
```

在**同一部手机**的 Chrome 中访问 `http://127.0.0.1:8126/`，点击开始录音、说中文指令、点击结束；Chrome 首次需要麦克风权限。由于页面通过 loopback 访问，WebAudio 和 `getUserMedia` 可以在支持的 Chrome 上使用，不需要公网 HTTPS。**不要修改 `server.py` 将服务绑定到 `0.0.0.0`**，实验接口没有用户登录，仅供本机试验。

停止方式：如果在 Termux 前台运行，按 `Ctrl+C`；如用 Termux 的后台任务启动，关闭对应 Termux session/作业即可，不要杀掉同机 HA Core `8125` 的 Python 进程。

## 指令候选（只预览）

- “打开客厅灯” → `turn_on / 客厅灯`
- “关闭客厅灯” → `turn_off / 客厅灯`
- “打开窗帘” → `turn_on / 窗帘`
- “关闭空调” → `turn_off / 空调`

语音解析逻辑为简单演示：只识别明确的**开/关**与目标关键词，不做模糊动作，不存音频或识别文字。未来如启用 HA 实际执行，必须增加实体 `entity_id` 白名单、用户授权、去抖、超时、安全确认与操作结果回执。不能把误识别直接映射到门锁、燃气、电源等高风险设备。

## 当前为什么使用独立页面而非官方 HA Assist

HA 官方 Assist 的安卓语音入口依赖配置好的 STT / Assist pipeline；本机要保证中文语音处理完全落在 ZUK 本地，不能仅凭客户端的按钮认定是离线识别。本实验先单独证明本地 ASR 运行，再考虑接入 HA 的 intents / Assist pipeline。

参考：[Vosk 官方模型](https://alphacephei.com/vosk/models) · [Vosk Android demo](https://github.com/alphacep/vosk-android-demo) · [HA Android Assist](https://www.home-assistant.io/voice_control/android/)
