import re

import torch
from torchao.quantization import Int8WeightOnlyConfig, quantize_
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageClassification,
    AutoTokenizer,
    ViTImageProcessor,
)


class ImageCheck:
    def __init__(self) -> None:
        self.model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
        self.processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
        self.model.eval()
        quantize_(self.model, Int8WeightOnlyConfig(version=2))

    async def predict(self, img):
        with torch.inference_mode():
            inputs = self.processor(images=img, return_tensors="pt")
            outputs = self.model(**inputs)
            logits = outputs.logits
        predicted_label = logits.argmax(-1).item()
        return self.model.config.id2label[predicted_label]


class TextCheck:
    def __init__(self, model_name: str = "Qwen/Qwen3Guard-Gen-0.6B"):
        # load the tokenizer and the model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
        self.model.eval()
        quantize_(self.model, Int8WeightOnlyConfig(version=2))

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
