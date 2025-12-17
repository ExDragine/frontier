import re

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_ID = "Falconsai/nsfw_image_detection"
MODEL_CAHCE_PATH = "./caches/models/"


class ImageCheck:
    def __init__(self) -> None:
        self.classifier = pipeline("image-classification", model="Falconsai/nsfw_image_detection", use_fast=True)

    async def predict(self, img):
        result = self.classifier(img)
        if isinstance(result, list):
            normal_score, nsfw_score = 0, 0
            for i in result:
                if i.get("label") == "normal":
                    normal_score = i.get("score", 0)
                else:
                    nsfw_score = i.get("score", 0)
            if float(normal_score) > float(nsfw_score):
                return {"label": "normal", "score": normal_score}
            else:
                return {"label": "nsfw", "score": nsfw_score}


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
