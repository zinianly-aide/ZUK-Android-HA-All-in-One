# ZUK 离线 ASR 对照测试：投影仪极光 AiAgent、SenseVoice INT8 与 Vosk

**日期**：2026-11-12
**设备**：ZUK Z2 Pro (`Z2121`)、Android 7.0 API 24、ARM64、Termux Python 3.14，原生 HA Core 2026.11.0 运行在端口 8125。
**目的**：确认能否直接利用投影仪提取的语音组件，实现完全在 ZUK 上的中文语音控制；并对比可用的开源离线 ASR。

## 1. 极光 AiAgent 的实机提取（只读）

投影仪运行 `com.ktcp.aiagent` `8.6.0.1069`，APK 约 12 MB，Android 9 / ARMv7。APK 内发现：

| 名称 | 大小 | 说明 |
|---|---:|---|
| `lib/armeabi-v7a/libAISpeech.so` | 120,424 B | 语音通信/处理相关本地库；不等于完整 ASR 模型 |
| `lib/armeabi-v7a/libAISpeechVad.so` | 1,308,200 B | 本地 VAD 相关实现 |
| `assets/AISpeech/VP/model/modelParameters.bin` | 547,208 B | 轻量模型参数，与 VAD/语音前端配置一起出现 |
| `featureMeanStd.bin` | 3,840 B | 声学特征统计 |

`assets/AISpeech/VP/model/tencentvideo.json` 包含 `vadMode`、`threshold`、`frame_shift_ms` 等前端语音相关字段。应用还有麦克风、联网权限及网络故障反馈资源。

**结论边界**：当前包内没有发现可独立测试、完整通用中文转文字的离线 ASR 模型与接口；但这不证明投影仪不可能从其他分区/运行时资源加载模型。**没有对投影仪断网执行语音测试**，所以极光的离线识别效果和识别耗时均为“未知”。另需厂商接口/授权才能复用专有组件，不应把从设备提取的 APK 或专有库上传公开仓库。

## 2. SenseVoice/ZUK Android 7 兼容性

- 官方 `sherpa-onnx` Android Demo `1.12.11`，包名 `com.k2fsa.sherpa.onnx.simulate.streaming.asr`，官方预编译 APK，SHA-256：`2cf0fddfe6186c6237f9337c3b0710261ef589211410942c644a3dae510587d4`。
- APK `minSdkVersion=21`，在 ZUK Android 7（24）安装成功。日志确认离线识别引擎初始化、Silero VAD 初始化成功，应用没有崩溃，麦克风权限已授予。
- Android Demo 模型初始化接近 13 秒（包括 App 初始化/文件准备）；运行时应用总 PSS 约 657 MiB。**这只是应用内存数据，不是单纯的模型权重大小。**
- 官方 `sherpa-onnx 2.0.1` Termux ARM64 预编译命令行程序可以在 ZUK 运行，配合隔离测试目录中的 Android NDK30 `libc++_shared.so` 与 `libonnxruntime.so`；不修改原 Termux 或系统共享库。
- INT8 模型 `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17`：`model.int8.onnx` 大小 239,233,841 字节，配套 `tokens.txt`。ZUK CLI 识别器初始化 **6.785 秒**；建议常驻加载，不要每条指令重新初始化。

模型和工具来源：

- [sherpa-onnx 官方 SenseVoice 模型说明](https://k2-fsa.github.io/sherpa/onnx/sense-voice/pretrained.html)
- [sherpa-onnx 官方 2.0.1 发布页](https://github.com/k2-fsa/sherpa-onnx/releases/tag/v2.0.1)
- [Android APK 公开索引](https://k2-fsa.github.io/sherpa/onnx/android/apk-simulate-streaming-asr.html)

## 3. 相同语音、同一台 ZUK 上的定量对照

测试语音由 Mac `say -v Tingting` 生成，再用 FFmpeg 转换为单声道 16 kHz PCM16 WAV；**不是真人声音**。SenseVoice 与 Vosk 使用相同的 5 个音频文件。SenseVoice 为 Android ARM64 CLI 两线程、模型预加载后依次解码 5 条；Vosk 为 ZUK 上已有的本机 Python HTTP 服务、模型常驻，每条独立请求。

| 口令原文 | SenseVoice INT8（ZUK） | Vosk small-cn-0.22（ZUK） | 识别判断 |
|---|---|---|---|
| 打开客厅灯 | 打开客厅灯。 | 打开 客厅 灯 | 两者正确 |
| 关闭窗帘 | 关闭窗帘。 | 关闭 窗帘 | 两者正确 |
| 把空调调到二十六度 | 把空调调到26度。 | 把 空调 调到 二十六 赌 | SenseVoice 正确，Vosk 错字 |
| 打开卧室灯 | 打开卧室灯。 | 打开 我 是 灯 | SenseVoice 正确，Vosk 错房间 |
| 请问今天的天气怎么样 | 请问今天的天气怎么样？ | 请问 今天 的 天气 怎么样 | 两者正确 |

**汇总（仅此 5 条合成语音）**：SenseVoice **5/5**，Vosk **3/5**，按同义数字/标点/空格归一化计。

| 同机性能指标 | SenseVoice INT8 | Vosk 中文小模型 |
|---|---:|---:|
| 5 条语音总计（11.967 秒音频） | **8.462 秒** | **23.405 秒** |
| 平均每条识别计算耗时 | **1.692 秒** | **4.681 秒** |
| 与音频长度的比率 RTF | **0.707** | **1.956**（按 23.405 / 11.967 估算） |
| 识别器初始化 | 6.785 秒 | 先前单独测试为约 0.98 秒 |
| 相对识别速度 | **约 2.77 倍于 Vosk** | 基线 |

不同调用链：Vosk 使用本地 HTTP 服务而 SenseVoice 使用 CLI，虽然都是 CPU 本机运行并已加载模型，但调用封装和请求开销不完全相同；此对照只能作为应用实验，不是标准 ASR 基准测试。Mac M4 的 SenseVoice 合成语音耗时为每条 **38–58 毫秒**，**不能**用于估算 ZUK 速度。

## 4. 与 HA 联动的实际结论

- 如果目标是 **ZUK 上真正离线普通话识别**，选择 **SenseVoice INT8**；优先采用常驻服务预加载模型，按键录音或本地唤醒，再做意图解析。
- 只在白名单中解析 HA 的普通灯光/窗帘等低风险实体，误识别或房间名称不明确时拒绝执行；特别是 Vosk “打开我是灯”可能导致泛化成错误的“打开灯”。
- 当前语音实验端口 `127.0.0.1:8126` 的 `actions_enabled` 仍为 `false`，不会调用 HA 服务控制家电。
- 后续必需验收：真人普通话、口音、背景电视噪声、麦克风远距离录音、重复 10–30 次的 P50/P95 延迟和热量/电量变化。
- 极光 AiAgent 想得到可比的数值，需要对原投影仪做可控的**断网语音功能测试**，或获得官方独立离线 ASR SDK 与授权。仅提取其 VAD 库不构成 ASR 对手。

**安全**：本文不上传任何投影仪固件 APK、厂商专有语音库、第三方模型权重、真实家庭设备实体/令牌、地址或麦克风录音。
