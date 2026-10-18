# 本地语音识别

Frontier 支持通过官方 FunASR C++ 运行器在 CPU 上运行 SenseVoiceSmall Q8。
识别按需启动子进程，结束后释放模型；没有额外的常驻 Python 推理服务。
该模型负责语音识别，不负责语音合成。

## Windows 安装

在项目根目录执行：

```powershell
uv sync --locked --group dev
uv run --locked python scripts/setup_sensevoice.py
```

安装器下载官方 `runtime-llamacpp-v0.2.1` Windows x64 通用 CPU 包、固定修订的
SenseVoiceSmall Q8 和 FSMN-VAD，并核对 SHA-256。只安装识别所需的可执行文件，
不执行下载内容。权重和运行器位于忽略提交的 `cache/speech/sensevoice/`，
来源和摘要记录在该目录的 `manifest.json`。
Q8 权重实际为 254,208,320 字节，VAD 为 1,720,512 字节。

确认 CPU 支持 AVX2、FMA、F16C、BMI2 时，可另装官方 AVX2 运行包：

```powershell
uv run --locked python scripts/setup_sensevoice.py --avx2
```

将下面配置中的 `executable` 改为
`cache/speech/sensevoice/runtime-avx2/llama-funasr-sensevoice.exe` 即可使用。
安装器同样核对官方 SHA-256，并将摘要写入 `manifest-avx2.json`。
不确定指令集支持时使用默认通用包；不要在不支持的 CPU 上使用 AVX2 包。

在 `env.toml` 添加以下配置并重启机器人；路径相对于启动工作目录，也可写绝对路径：

```toml
[speech_recognition]
enabled = true
executable = "cache/speech/sensevoice/runtime/llama-funasr-sensevoice.exe"
model_path = "cache/speech/sensevoice/sensevoice-small-q8.gguf"
vad_model_path = "cache/speech/sensevoice/fsmn-vad.gguf"
max_cpu_cores = 4
timeout_seconds = 120
max_audio_seconds = 120
max_audio_bytes = 10485760
max_audio_per_message = 3
max_transcript_chars = 8000
```

`enabled` 默认关闭；缺少或无效的运行器路径会返回明确的失败提示。
`max_cpu_cores` 限制逻辑 CPU 亲和性，不会修改 C++ 运行器内部的线程数。
Windows 子进程隐藏窗口并使用低于普通级别的优先级。请求全局串行，
`timeout_seconds` 包含排队、格式转换、模型加载和推理；超时或取消会杀死并回收子进程。
在没有进程 CPU 亲和性功能的平台上，逻辑 CPU 限制不可用。

其他平台可自行安装相应的官方 C++ CPU 运行器，再配置同一组路径；本安装脚本仅支持 Windows x64。

## 消息行为

- 只有已经通过现有 Agent 回复网关的当前语音才下载和识别。不会为了检测语音中的唤醒词扫描所有群语音。
- 原始语音按原有规则保存为附件。转写标记为用户语音的派生文本，进入内容检查和本轮 Agent 输入。
- 转写通过已有消息归一化更新接口写入当前消息的正文，保留原始消息段并更新现有 FTS 索引，后续历史可读取。
- 启用本地识别后，当前语音不再重复内联给主模型；未启用时保留原来的原生音频路径。
- 当前引用/历史语音附件不会自动识别；此版本处理本轮直接收到的语音。
- QQ SILK 使用锁定的 `silk-python` 在隔离子进程中解码。其他格式由项目自带 FFmpeg 转换为 16kHz、单声道 PCM16。
- 解码拒绝播放列表及网络协议，限制输入体积、输出时长和文本长度。识别失败保留原始附件及其他文字，并明确标注无法理解该语音。
- 日志只记录错误码、时长和字符数，不打印语音内容、转写正文或运行器 stderr。

## 复现资源测量

指定公开样本或明确选定的测试音频：

```powershell
uv run --locked python scripts/benchmark_sensevoice.py --audio path/to/test.mp3 --cores 4 --output .temp/sensevoice-benchmark
```

测量 AVX2 包时，追加
`--executable cache/speech/sensevoice/runtime-avx2/llama-funasr-sensevoice.exe`。

脚本使用独立临时配置，不读取生产 `env.toml`，输出 `report.html` 和 `report.json`。
用例包含 MP3 首次/重复请求、真实腾讯格式 SILK、30/120 秒合成压力样本、2/4 请求排队、静音和超长拒绝。
报告区分总延迟、RTF、采样 CPU 时间、进程树 RSS 和 Windows 私有内存。
按需 CLI 路径的模型加载开销包含在每次请求中；重复调用可能受操作系统文件缓存影响。

硬件、系统和测试边界写入报告。开发机的结果不能当作不同 CPU、8GB 内存目标机的实测，
也不能代表包含 QQ、浏览器和机器人服务的整机峰值。

本次交付的[资源压力报告](reports/sensevoice-q8-2026-10-18.html)和
[原始数据](reports/sensevoice-q8-2026-10-18.json)比较了通用 CPU 与 AVX2 运行包。

官方来源：

- [SenseVoice Q8 权重](https://huggingface.co/FunAudioLLM/SenseVoiceSmall-GGUF)
- [官方 C++ 运行器发布](https://github.com/QwenAudio/SenseVoice/releases/tag/runtime-llamacpp-v0.2.1)
- [SILK 解码依赖](https://pypi.org/project/silk-python/)
