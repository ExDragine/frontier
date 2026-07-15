from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from .types import (
    ApiMode,
    LocalizedDescription,
    ModelCapabilities,
    ModelCard,
    ModelCatalog,
    ModelFeature,
    ModelInput,
    ModelOutput,
    ModelSource,
    ModelStatus,
)


def _parse_model(provider: str, raw: dict[str, Any]) -> ModelCard:
    capabilities = raw["capabilities"]
    description = raw["description"]
    return ModelCard(
        provider=provider,
        id=raw["id"],
        display_name=raw["display_name"],
        description=LocalizedDescription(en=description["en"], zh_cn=description["zh-CN"]),
        capabilities=ModelCapabilities(
            input=tuple(ModelInput(item) for item in capabilities["input"]),
            output=tuple(ModelOutput(item) for item in capabilities["output"]),
            features=tuple(ModelFeature(item) for item in capabilities["features"]),
            api_modes=tuple(ApiMode(item) for item in capabilities["api_modes"]),
        ),
        context_window=raw["context_window"],
        max_output_tokens=raw["max_output_tokens"],
        knowledge_cutoff=raw["knowledge_cutoff"],
        released_at=raw["released_at"],
        status=ModelStatus(raw["status"]),
        sources=tuple(ModelSource(**source) for source in raw["sources"]),
    )


@lru_cache(maxsize=1)
def load_catalog() -> ModelCatalog:
    """Load and parse the catalog stored in the project models module."""
    package = files("models")
    resource = package.joinpath("data/catalog.json")
    with resource.open("r", encoding="utf-8") as catalog_file:
        raw = json.load(catalog_file)

    models: list[ModelCard] = []
    for provider_entry in raw["providers"]:
        provider_resource = package.joinpath(f"data/{provider_entry['file']}")
        with provider_resource.open("r", encoding="utf-8") as provider_file:
            provider_data = json.load(provider_file)
        if provider_data["provider"] != provider_entry["id"]:
            raise ValueError(f"Provider mismatch in {provider_entry['file']}")
        models.extend(_parse_model(provider_data["provider"], model) for model in provider_data["models"])

    return ModelCatalog(
        schema_version=raw["schema_version"],
        catalog_version=raw["catalog_version"],
        updated_at=raw["updated_at"],
        models=tuple(models),
    )


def get_model(provider: str, model_id: str) -> ModelCard | None:
    """Return a model card, or ``None`` when the model is not cataloged."""
    provider_key = provider.strip().lower()
    model_key = model_id.strip().lower()
    return next(
        (
            model
            for model in load_catalog().models
            if model.provider == provider_key and model.id.lower() == model_key
        ),
        None,
    )


def list_models(
    provider: str | None = None,
    feature: ModelFeature | str | None = None,
    status: ModelStatus | str | None = "active",
) -> tuple[ModelCard, ...]:
    """List models matching the optional provider, feature, and status filters."""
    provider_key = provider.strip().lower() if provider is not None else None
    feature_key = ModelFeature(feature) if feature is not None else None
    status_key = ModelStatus(status) if status is not None else None
    return tuple(
        model
        for model in load_catalog().models
        if (provider_key is None or model.provider == provider_key)
        and (feature_key is None or feature_key in model.capabilities.features)
        and (status_key is None or model.status is status_key)
    )
