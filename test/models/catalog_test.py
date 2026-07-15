from __future__ import annotations

# ruff: noqa: S101
import json
from importlib.resources import files
from urllib.parse import urlparse

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from models import (
    ModelFeature,
    ModelStatus,
    get_model,
    list_models,
    load_catalog,
)


def _load_resource(name: str) -> dict:
    resource = files("models").joinpath(f"data/{name}")
    with resource.open("r", encoding="utf-8") as resource_file:
        return json.load(resource_file)


def test_catalog_matches_json_schema() -> None:
    catalog = _load_resource("catalog.json")
    catalog_schema = _load_resource("catalog.schema.json")
    provider_schema = _load_resource("provider.schema.json")

    Draft202012Validator(catalog_schema, format_checker=FormatChecker()).validate(catalog)
    provider_ids = [entry["id"] for entry in catalog["providers"]]
    provider_files = [entry["file"] for entry in catalog["providers"]]
    assert len(provider_ids) == len(set(provider_ids))
    assert len(provider_files) == len(set(provider_files))
    actual_files = {
        f"providers/{resource.name}"
        for resource in files("models").joinpath("data/providers").iterdir()
        if resource.name.endswith(".json")
    }
    assert set(provider_files) == actual_files
    for provider_entry in catalog["providers"]:
        provider_data = _load_resource(provider_entry["file"])
        Draft202012Validator(provider_schema, format_checker=FormatChecker()).validate(provider_data)
        assert provider_data["provider"] == provider_entry["id"]


def test_catalog_invariants() -> None:
    catalog = _load_resource("catalog.json")
    identities: set[tuple[str, str]] = set()
    official_hosts = {
        "ai21": {"docs.ai21.com"},
        "antgroup": {"developer.ant-ling.com"},
        "anthropic": {"platform.claude.com"},
        "baichuan": {"platform.baichuan-ai.com", "www.baichuan-ai.com"},
        "cohere": {"docs.cohere.com"},
        "deepseek": {"api-docs.deepseek.com"},
        "google": {"ai.google.dev"},
        "groq": {"console.groq.com"},
        "hunyuan": {"cloud.tencent.com"},
        "internlm": {"internlm.intern-ai.org.cn"},
        "jina": {"jina.ai"},
        "longcat": {"longcat.chat"},
        "minimax": {"platform.minimaxi.com"},
        "mistral": {"docs.mistral.ai"},
        "moonshot": {"platform.kimi.ai", "www.kimi.com"},
        "nvidia": {"build.nvidia.com"},
        "openai": {"developers.openai.com"},
        "perplexity": {"docs.perplexity.ai", "www.perplexity.ai"},
        "qwen": {"help.aliyun.com"},
        "spark": {"www.xfyun.cn"},
        "stepfun": {"platform.stepfun.com"},
        "upstage": {"console.upstage.ai", "www.upstage.ai"},
        "v0": {"v0.dev", "vercel.com"},
        "volcengine": {"www.volcengine.com"},
        "wenxin": {"cloud.baidu.com"},
        "xai": {"docs.x.ai"},
        "xiaomimimo": {"mimo.mi.com"},
        "zhipu": {"docs.bigmodel.cn"},
    }
    assert set(official_hosts) == {entry["id"] for entry in catalog["providers"]}

    for provider_entry in catalog["providers"]:
        provider_data = _load_resource(provider_entry["file"])
        provider = provider_data["provider"]
        for model in provider_data["models"]:
            identity = (provider, model["id"].lower())
            assert identity not in identities
            identities.add(identity)

            assert model["description"]["en"].strip()
            assert model["description"]["zh-CN"].strip()
            assert "text" in model["capabilities"]["input"]
            assert model["sources"]
            assert all(source["url"].startswith("https://") for source in model["sources"])
            assert all(urlparse(source["url"]).hostname in official_hosts[provider] for source in model["sources"])
            assert all(source["verified_at"] for source in model["sources"])
            assert all(source["verified_at"] <= catalog["updated_at"] for source in model["sources"])
            for field in ("context_window", "max_output_tokens"):
                assert model[field] is None or model[field] > 0


def test_load_catalog_returns_frozen_typed_data() -> None:
    catalog = load_catalog()
    manifest = _load_resource("catalog.json")
    expected_model_count = sum(len(_load_resource(entry["file"])["models"]) for entry in manifest["providers"])

    assert catalog.schema_version == "1.1"
    assert catalog.catalog_version == "2026.7.15"
    assert len(catalog.models) == expected_model_count
    with pytest.raises(AttributeError):
        catalog.updated_at = "2000-01-01"  # type: ignore[misc]


def test_get_model_and_unknown_model() -> None:
    model = get_model(" OpenAI ", "GPT-5.6-SOL")
    canonical_case_model = get_model("antgroup", "ling-2.6-1t")

    assert model is not None
    assert model.display_name == "GPT-5.6 Sol"
    assert model.status is ModelStatus.ACTIVE
    assert canonical_case_model is not None
    assert canonical_case_model.id == "Ling-2.6-1T"
    assert get_model("custom", "private-model") is None


def test_list_models_filters_provider_feature_and_status() -> None:
    active_google = list_models(provider="google")
    preview_google = list_models(provider="google", status=ModelStatus.PREVIEW)
    image_generation = list_models(feature=ModelFeature.IMAGE_GENERATION)

    assert active_google
    assert all(model.provider == "google" and model.status is ModelStatus.ACTIVE for model in active_google)
    assert preview_google
    assert all(model.provider == "google" and model.status is ModelStatus.PREVIEW for model in preview_google)
    assert image_generation
    assert all(ModelFeature.IMAGE_GENERATION in model.capabilities.features for model in image_generation)
    assert all(model.status is ModelStatus.ACTIVE for model in list_models())
    assert len(list_models(status=None)) == len(load_catalog().models)


def test_list_models_rejects_unknown_controlled_values() -> None:
    with pytest.raises(ValueError):
        list_models(feature="unknown")
    with pytest.raises(ValueError):
        list_models(status="unknown")
