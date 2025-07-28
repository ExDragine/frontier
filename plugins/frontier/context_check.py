import torch
from transformers import AutoModelForImageClassification, ViTImageProcessor


async def context_checker(image):
    # 确保 image 为 RGB 格式
    if hasattr(image, "mode") and image.mode != "RGB":
        image = image.convert("RGB")
    model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
    processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
    with torch.no_grad():
        inputs = processor(image, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits
    predicted_label = logits.argmax(-1).item()
    return model.config.id2label[predicted_label]
