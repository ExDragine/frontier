import os
import re

import numpy as np
import onnxruntime as ort
from nonebot import logger
from PIL import Image
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, ViTImageProcessor

from utils.onnx import export_to_onnx

MODEL_ID = "Falconsai/nsfw_image_detection"
MODEL_CAHCE_PATH = "./cache/models/"


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    m = np.max(x, axis=axis, keepdims=True)
    e = np.exp(x - m)
    return e / np.sum(e, axis=axis, keepdims=True)


def _choose_providers(prefer_cuda: bool = True) -> list[str]:
    avail = ort.get_available_providers()
    if prefer_cuda and "CUDAExecutionProvider" in avail:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if "ROCMExecutionProvider" in avail:
        return ["ROCMExecutionProvider", "CPUExecutionProvider"]
    if "DmlExecutionProvider" in avail:  # Windows DirectML
        return ["DmlExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


def _onnx_options():
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.enable_mem_pattern = True
    so.enable_cpu_mem_arena = True
    so.intra_op_num_threads = 0
    so.inter_op_num_threads = 1
    return so


class ImageCheck:
    def __init__(self, model_id: str = MODEL_ID, model_path: str = MODEL_CAHCE_PATH, batch_size: int = 4) -> None:
        self.onnx_model = f"{model_path}model_int8_dyn.onnx"
        self.batch_size = batch_size
        self.processor = ViTImageProcessor.from_pretrained(model_id)
        cfg = AutoConfig.from_pretrained(model_id)
        self.id2label = dict(getattr(cfg, "id2label", {}))
        providers = _choose_providers()
        logger.info(f"[ONNX Runtime] Providers: {providers}")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        if not os.path.exists(self.onnx_model):
            export_to_onnx(model_id, model_path)
        self.session = ort.InferenceSession(self.onnx_model, sess_options=_onnx_options(), providers=providers)

    @staticmethod
    def _ensure_rgb(img: Image.Image | np.ndarray):
        if isinstance(img, np.ndarray):
            if img.ndim == 2:
                img = np.stack([img, img, img], axis=-1)
            if img.shape[-1] != 3:
                raise ValueError("ndarray image must be (H,W,3)")
            return Image.fromarray(img.astype(np.uint8)).convert("RGB")
        return img.convert("RGB") if getattr(img, "mode", None) != "RGB" else img

    def _preprocess_batch(self, imgs: list[Image.Image | np.ndarray]) -> np.ndarray:
        pil_imgs = [self._ensure_rgb(im) for im in imgs]
        inputs = self.processor(pil_imgs, return_tensors="np")
        return inputs["pixel_values"].astype(np.float32)  # (B,3,224,224)

    def predict(self, images: Image.Image | np.ndarray | list[Image.Image | np.ndarray]):
        if not isinstance(images, list | tuple):
            images = [images]

        results = []
        for i in range(0, len(images), self.batch_size):
            batch_imgs = images[i : i + self.batch_size]
            pixel_values = self._preprocess_batch(batch_imgs)
            logits = self.session.run(None, {"pixel_values": pixel_values})[0]  # (B,C)
            probs = _softmax(logits, axis=-1)  # type: ignore
            top = probs.argmax(axis=-1)
            for j, cls in enumerate(top):
                results.append(
                    {
                        "label": self.id2label.get(int(cls), str(int(cls))),
                        "score": float(probs[j, cls]),
                        "logits": logits[j].tolist(),  # type: ignore
                        "probs": probs[j].tolist(),
                    }
                )
        return results


class TextCheck:
    def __init__(self, model_name: str = "Qwen/Qwen3Guard-Gen-0.6B"):
        # load the tokenizer and the model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")

    def extract_label_and_categories(self, content):
        safe_pattern = r"Safety: (Safe|Unsafe|Controversial)"
        category_pattern = r"(Violent|Non-violent Illegal Acts|Sexual Content or Sexual Acts|PII|Suicide & Self-Harm|Unethical Acts|Politically Sensitive Topics|Copyright Violation|Jailbreak|None)"
        safe_label_match = re.search(safe_pattern, content)  # type: ignore
        label = safe_label_match.group(1) if safe_label_match else None
        categories = re.findall(category_pattern, content)  # type: ignore
        return label, categories

    async def predict(self, prompt: str):
        # for prompt moderation
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # conduct text completion
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=128)
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()

        content = self.tokenizer.decode(output_ids, skip_special_tokens=True)

        safe_label, categories = self.extract_label_and_categories(content)
        return (safe_label, categories)


det = ImageCheck(MODEL_ID)
text_det = TextCheck()
