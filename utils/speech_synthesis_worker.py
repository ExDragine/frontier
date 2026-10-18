"""One-shot CPU inference worker. No bot configuration or weights load on import."""

import argparse
import io
import json
import math
import os
import subprocess
import sys
import time
import wave
from pathlib import Path


def synthesize(request_path: Path) -> None:
    started = time.monotonic()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    directory = request_path.parent
    root = Path(request["model_dir"]).resolve()
    cores = int(request["max_cpu_cores"])
    os.environ.update(
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_MODULES_CACHE=str(directory / "modules"),
        OMP_NUM_THREADS=str(cores),
        MKL_NUM_THREADS=str(cores),
        TOKENIZERS_PARALLELISM="false",
    )
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from utils.moss_tts_assets import verify_installation

    verify_installation(root)

    import imageio_ffmpeg
    import pysilk
    import torch
    from transformers import AutoConfig, AutoModel
    from transformers.dynamic_module_utils import get_class_from_dynamic_module

    torch.set_num_threads(cores)
    torch.set_num_interop_threads(1)
    torch.manual_seed(42)
    # The official zh_1.wav asset contains FLAC data despite its extension.
    reference_path = directory / "reference.wav"
    subprocess.run(  # noqa: S603
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-threads",
            "1",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(root / "runtime/assets/audio/zh_1.wav"),
            "-t",
            "30",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            str(reference_path),
        ],
        check=True,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    tts_directory = root / "MOSS-TTS-Nano-100M"
    config = AutoConfig.from_pretrained(tts_directory, trust_remote_code=True, local_files_only=True)
    config.attn_implementation = "sdpa"
    config.local_transformer_attn_implementation = "sdpa"
    model_class = get_class_from_dynamic_module(
        config.auto_map["AutoModelForCausalLM"],
        tts_directory,
        local_files_only=True,
    )
    # Construct on CPU so upstream nonpersistent RoPE buffers are initialized.
    # Transformers 5's meta-device loader leaves those custom buffers empty.
    model = model_class(config)
    checkpoint = torch.load(tts_directory / "pytorch_model.bin", map_location="cpu", weights_only=True)
    checkpoint.pop("local_transformer.wte.weight", None)  # Removed by the upstream model constructor.
    model.load_state_dict(checkpoint, strict=True)
    del checkpoint
    model.eval()
    codec = AutoModel.from_pretrained(
        root / "MOSS-Audio-Tokenizer-Nano",
        trust_remote_code=True,
        local_files_only=True,
        dtype=torch.float32,
    ).eval()
    codec.set_attention_implementation("sdpa")
    codec.set_compute_dtype("fp32")
    wav_path = directory / "output.wav"
    with torch.inference_mode():
        model.inference(
            text=request["text"],
            output_audio_path=wav_path,
            mode="voice_clone",
            prompt_audio_path=reference_path,
            text_tokenizer_path=str(tts_directory),
            audio_tokenizer=codec,
            device="cpu",
            max_new_frames=math.ceil(request["max_audio_seconds"] * 12.5) + 1,
            voice_clone_max_text_tokens=75,
            voice_clone_max_memory_per_sample_gb=1.0,
            tts_max_batch_size=1,
            codec_max_batch_size=1,
            do_sample=True,
            use_kv_cache=True,
            text_temperature=1.0,
            text_top_p=1.0,
            text_top_k=50,
            audio_temperature=0.8,
            audio_top_p=0.95,
            audio_top_k=25,
            audio_repetition_penalty=1.2,
        )
    with wave.open(str(wav_path), "rb") as audio:
        seconds = audio.getnframes() / audio.getframerate()
        sample_rate = audio.getframerate()
    if not 0.1 <= seconds <= request["max_audio_seconds"]:
        raise ValueError("Generated audio duration exceeds limit")
    pcm_path = directory / "voice.pcm"
    subprocess.run(  # noqa: S603
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-threads",
            "1",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(wav_path),
            "-ac",
            "1",
            "-ar",
            "24000",
            "-f",
            "s16le",
            str(pcm_path),
        ],
        check=True,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    output = io.BytesIO()
    pysilk.encode(io.BytesIO(pcm_path.read_bytes()), output, 24000, 24000, tencent=True)
    (directory / "output.silk").write_bytes(output.getvalue())
    (directory / "result.json").write_text(
        json.dumps(
            {
                "audio_seconds": seconds,
                "sample_rate": sample_rate,
                "elapsed_seconds": time.monotonic() - started,
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    synthesize(parser.parse_args().request)
