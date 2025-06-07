import asyncio

import torch
from PIL import Image
from transformers import AutoModelForImageClassification, ViTImageProcessor


async def context_check(image):
    model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
    processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
    with torch.no_grad():
        inputs = processor(image, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits
    predicted_label = logits.argmax(-1).item()
    return model.config.id2label[predicted_label]
