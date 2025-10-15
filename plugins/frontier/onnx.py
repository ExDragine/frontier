import os

import onnx
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.shape_inference import quant_pre_process
from transformers import AutoConfig, AutoModelForImageClassification


def export_to_onnx(model_id, onnx_path, opset: int = 17, force: bool = False):
    if os.path.exists(f"{onnx_path}model_int8_dyn.onnx") and not force:
        return onnx_path
    cfg = AutoConfig.from_pretrained(model_id)
    image_size = int(getattr(cfg, "image_size", 224))
    model = AutoModelForImageClassification.from_pretrained(model_id)
    model.eval()
    dummy = torch.randn(1, 3, image_size, image_size, dtype=torch.float32)
    torch.onnx.export(
        model,
        {"pixel_values": dummy},  # type: ignore
        f=f"{onnx_path}origin.onnx",
        input_names=["pixel_values"],
        output_names=["logits"],
        dynamic_axes={"pixel_values": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=opset,
        do_constant_folding=True,
    )
    onnx_path = optimize_model(onnx_path)
    return onnx_path


def optimize_model(model_path):
    quant_pre_process(f"{model_path}origin.onnx", f"{model_path}model_optimized.onnx")
    quantize_dynamic(
        model_input=f"{model_path}model_optimized.onnx",
        model_output=f"{model_path}model_int8_dyn.onnx",
        op_types_to_quantize=["MatMul", "Gemm"],
        per_channel=True,
        weight_type=QuantType.QInt8,
        extra_options={
            "DefaultTensorType": onnx.TensorProto.FLOAT,
            "MatMulConstBOnly": True,
        },
    )

    return f"{model_path}model_int8_dyn.onnx"
