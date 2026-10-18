# 本地语音合成

使用 [MOSS-TTS-Nano-100M](https://huggingface.co/OpenMOSS-Team/MOSS-TTS-Nano-100M)
及其官方 Nano 音频编解码器，在 CPU 上按需合成语音。选择原生 PyTorch 版，
复用项目已有的 Torch、Transformers、FFmpeg 和 SILK 库，新增依赖仅 SentencePiece。

## 安装与试听

依赖已包含在 uv 默认安装中。启用 `[speech_synthesis].enabled = true` 后，
首次有效合成请求自动下载并校验资源，无需先执行安装脚本。
未启用或原文为空/超限时不会下载。

在项目根目录执行即可安装依赖并试听（试听也会自动下载）：

```powershell
uv sync --locked --group dev
uv run --locked python scripts/preview_moss_tts.py
```

也可用 `uv run --locked python scripts/setup_speech.py` 一次预下载识别和合成资源，
或用原来的 `scripts/setup_moss_tts.py` 只准备合成。安装器只下载并校验文件，不运行模型。
固定修订、官方地址和 SHA-256 位于 `utils/moss_tts_assets.json`。两个模型的权重合计 322,615,663 字节；
模型代码、分词器和官方 Junhao 中文男声参考也一并安装到 `cache/speech/moss-tts/`。
上游许可证保存在安装目录的 `runtime/LICENSE`。

试听脚本使用隔离的临时配置，不读取机器人真实配置，不向 QQ 发送消息。
生成 `cache/speech/previews/moss-native.wav`、同名 SILK 和 JSON 测量记录。
也可指定原文和输出前缀：

```powershell
uv run --locked python scripts/preview_moss_tts.py --text "你好，今天过得怎么样？" --output cache/speech/previews/greeting
```

模型默认使用官方中文男声 Junhao。本次不提供用户音色克隆或任意参考音频上传。

## 启用 Agent 工具

在 `env.toml` 添加以下配置并重新加载配置或重启机器人：

```toml
[speech_synthesis]
enabled = true
auto_download = true
download_timeout_seconds = 600
model_dir = "cache/speech/moss-tts"
voice = "Junhao"
max_cpu_cores = 4
timeout_seconds = 180
max_text_chars = 300
max_audio_seconds = 60
rate_limit_max_requests = 3
rate_limit_window_seconds = 600
```

相对路径以机器人启动目录为基准。`voice` 当前只接受 `Junhao`。
用户明确要求“用语音说”“朗读这句话”时，Agent 可调用 `get_speech(text)`。
QQ 接收 24 kHz 单声道 Tencent SILK 语音；试听 WAV 保留原生 48 kHz 双声道。
工件由现有投递链路自动发送，模型无需再调用 `send_voice`，也不接收可执行文件或模型路径参数。
工具共用 `[paint_policy]` 白名单和黑名单；本节的用户限频独立于绘画、视频。

## 资源与故障行为

- 每次请求使用独立 Python 子进程，结束后释放模型；空闲时不保留额外模型进程。
- 与 SenseVoice 识别共享全局锁，避免两个模型同时加载。限额包含排队、初始化、推理及编码。
- 首次资源准备单独限时 600 秒，包含等待下载锁；同一资源的多个进程通过文件锁避免重复写入。
  下载先写临时文件，校验成功后原子替换。关闭 `auto_download` 可使用预装资源离线运行。
- 默认 Torch 使用 4 个计算线程、1 个 inter-op 线程；支持亲和性的平台同时限制逻辑 CPU。
  Windows 隐藏窗口并使用低于普通级别的优先级。
- 超时或取消会回收整个子进程树。文本或音频超限时返回明确错误，不静默截掉原文。
- 失败只记录静态错误码、耗时和长度，不记录待朗读正文。生成失败时可继续文字回复。
  `asset_download_failed` / `asset_download_timeout` 可在网络恢复后重试或预先运行安装命令；
  离线模式的 `runtime_missing_or_unverified` 需要预装资源；`timeout` 可缩短原文或调整推理超时。
- 一次短句测量无法证明在 8 GB 主机上长期运行的余量；试听 JSON 记录本次主机和子进程峰值 RSS，
  实际部署还需加上机器人、浏览器及系统的占用。

### 2026-10-19 本机试听测量

Windows 11、AMD CPU、31.16 GiB 内存，推理限制为 4 个逻辑 CPU；
Torch 2.14.1+cpu、Transformers 5.18.0、SentencePiece 0.2.2。
两次均重新启动推理子进程，耗时包含加载和编码。峰值为每 50 ms 采样的子进程树 RSS，
不包含机器人主进程或整个系统占用。

| 试听 | 音频时长 | 总耗时 | 峰值 RSS | 总耗时 / 音频时长 |
| --- | --- | --- | --- | --- |
| 问候短句 | 5.84 秒 | 15.46 秒 | 1130.76 MiB | 2.65 |
| 较长说明 | 12.24 秒 | 22.27 秒 | 1265.70 MiB | 1.82 |

两段 WAV 及其 SILK 都用本地 SenseVoiceSmall Q8 回验，正文一致（短句“小芙”转写为同音“小福”）。
这只是短句与段落的试听资源快照，不是 8 GB Intel 目标机的压力测试或实时性能承诺。
目标机建议先保持单请求和 4 核限制，用同一试听命令复测。

## 原生模型兼容适配

上游只在文件读写和重采样时引用 torchaudio。安装器保存校验过的原始模型文件为
`modeling_moss_tts_nano.py.upstream`，仅将该导入替换成仓库内的 WAV I/O 适配器。
固定参考素材虽然名为 `.wav`，内容实际是 FLAC，先由现有 FFmpeg 转换。
每次执行前重新核对所有模型代码、配置、分词器、参考音频和适配器；自动准备会对权重完整校验，
并缓存文件状态，文件发生变化时重新校验。
推理关闭 Hub 网络访问并只从本地加载，子进程的动态模块缓存随请求清理。

主模型直接在 CPU 构造并严格加载 `weights_only=True` 的权重，保留上游 RoPE 非持久缓冲区的初始化，
避免 Transformers 5 的 meta-device 加载导致这些缓冲区未初始化。全局、局部解码器使用 CPU SDPA。
