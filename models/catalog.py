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

# Author identifiers are name lookup aliases, never model routing rules.
_NAME_PROVIDER_ALIASES = {
    "mistralai": "mistral",
    "moonshotai": "moonshot",
    "x-ai": "xai",
    "xiaomi": "xiaomimimo",
    "z-ai": "zhipu",
}


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


@lru_cache(maxsize=1)
def _load_lobehub_names() -> dict[str, dict[str, str]]:
    resource = files("models").joinpath("data/lobehub_names.json")
    with resource.open("r", encoding="utf-8") as names_file:
        raw = json.load(names_file)
    providers = raw.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("LobeHub model names snapshot has no providers")
    return {
        str(provider).casefold(): {
            str(model_id).casefold(): str(display_name)
            for model_id, display_name in models.items()
            if isinstance(display_name, str) and display_name.strip()
        }
        for provider, models in providers.items()
        if isinstance(models, dict)
    }


def _model_id_candidates(model_id: str) -> tuple[str, ...]:
    parts = model_id.strip().split("/")
    candidates = []
    for index in range(len(parts)):
        candidate = "/".join(parts[index:]).casefold()
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return tuple(candidates)


@lru_cache(maxsize=1)
def _load_openrouter_names() -> dict[str, str]:
    resource = files("models").joinpath("data/openrouter_names.json")
    try:
        with resource.open("r", encoding="utf-8") as names_file:
            raw = json.load(names_file)
    except FileNotFoundError:
        return {}
    models = raw.get("models")
    if not isinstance(models, dict):
        raise ValueError("OpenRouter model names snapshot has no models")
    return {
        model_id.casefold(): display_name
        for model_id, display_name in models.items()
        if isinstance(display_name, str) and display_name.strip()
    }


def _name_provider(provider: str) -> str:
    return _NAME_PROVIDER_ALIASES.get(provider, provider)


def _name_identity(
    provider: str,
    candidates: tuple[str, ...],
    openrouter_names: dict[str, str],
    lobehub_names: dict[str, dict[str, str]],
) -> tuple[str, str, str | None]:
    for candidate in candidates:
        if candidate in openrouter_names:
            author, _, slug = candidate.partition("/")
            return _name_provider(author), slug, candidate
    authors = (
        {model.provider for model in load_catalog().models}
        | {key.partition("/")[0] for key in openrouter_names}
        | lobehub_names.keys()
        | _NAME_PROVIDER_ALIASES.keys()
    )

    # An explicit author wins over the adapter type (often "openai" for proxies).
    for candidate in candidates:
        author, separator, slug = candidate.partition("/")
        if separator and author in authors:
            return _name_provider(author), slug, candidate
    return _name_provider(provider.strip().casefold()), candidates[0], None


def _openrouter_display_name(
    provider: str, model_key: str, qualified_id: str | None, names: dict[str, str], allow_global: bool
) -> str | None:
    if qualified_id is not None and (display_name := names.get(qualified_id)):
        return display_name
    matches = [
        name
        for key, name in names.items()
        if (parts := key.partition("/"))[2] == model_key and _name_provider(parts[0]) == provider
    ]
    if len(matches) == 1:
        return matches[0]
    if allow_global:
        matches = [name for key, name in names.items() if key.partition("/")[2] == model_key]
        if len(matches) == 1:
            return matches[0]
    return None


def get_model_display_name(provider: str, model_id: str) -> str:
    """Resolve local, OpenRouter, then LobeHub names without changing capabilities."""
    candidates = _model_id_candidates(model_id)
    if not candidates:
        return model_id
    openrouter_names = _load_openrouter_names()
    lobehub_names = _load_lobehub_names()
    provider_key, model_key, qualified_id = _name_identity(provider, candidates, openrouter_names, lobehub_names)
    allow_global = (
        qualified_id is None
        and "/" not in model_key
        and sum(key.partition("/")[2] == model_key for key in openrouter_names) <= 1
    )

    if card := get_model(provider_key, model_key):
        return card.display_name
    if allow_global:
        matches = [model for model in load_catalog().models if model.id.casefold() == model_key]
        if len(matches) == 1:
            return matches[0].display_name

    if display_name := _openrouter_display_name(provider_key, model_key, qualified_id, openrouter_names, allow_global):
        return display_name
    provider_names = lobehub_names.get(provider_key, {})
    if display_name := provider_names.get(model_key):
        return display_name
    if allow_global:
        matches = {
            display_name.casefold(): display_name
            for models in lobehub_names.values()
            if (display_name := models.get(model_key))
        }
        if len(matches) == 1:
            return next(iter(matches.values()))
    return model_id


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
