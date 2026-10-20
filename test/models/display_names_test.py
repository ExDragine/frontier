from __future__ import annotations

# ruff: noqa: S101
from dataclasses import replace

import pytest

from models import catalog as catalog_module
from models import get_model, get_model_display_name, load_catalog


@pytest.fixture
def name_overlays(monkeypatch):
    monkeypatch.setattr(
        catalog_module,
        "_load_openrouter_names",
        lambda: {
            "alpha/shared": "Alpha: Shared",
            "beta/shared": "Beta: Shared",
            "alpha/shared:free": "Alpha: Shared (free)",
            "alpha/unique": "Alpha: Unique",
            "alpha/org/model": "Alpha: Nested Model",
            "openrouter/auto": "Auto Router",
            "~alpha/shared": "Alpha: Shared Router",
            "openai/gpt-5.6-sol": "Upstream GPT Name",
            "moonshotai/kimi-example": "MoonshotAI: Kimi Example",
            "z-ai/glm-example": "Z.ai: GLM Example",
            "anthropic/claude-example.1": "Anthropic: Claude Example 1",
        },
    )
    monkeypatch.setattr(
        catalog_module,
        "_load_lobehub_names",
        lambda: {
            "alpha": {"unique": "Old Unique Name", "shared": "Old Shared Name"},
            "openai": {"gpt-5.6-sol": "Old GPT Name"},
            "legacy": {"fallback": "Legacy Name"},
        },
    )


@pytest.mark.usefixtures("name_overlays")
@pytest.mark.parametrize("model_id", ["gpt-5.6-sol", "openai/gpt-5.6-sol", "gateway/openai/gpt-5.6-sol"])
def test_verified_local_names_override_both_external_sources(model_id) -> None:
    assert get_model_display_name("openai", model_id) == "GPT-5.6 Sol"


@pytest.mark.usefixtures("name_overlays")
@pytest.mark.parametrize(
    "model_id", ["unique", "alpha/unique", "gateway/alpha/unique", "openrouter/alpha/unique", " ALPHA/UNIQUE "]
)
def test_openrouter_precedes_lobehub_and_supports_qualified_and_unique_ids(model_id) -> None:
    assert get_model_display_name("openai", model_id) == "Alpha: Unique"


@pytest.mark.usefixtures("name_overlays")
def test_explicit_author_wins_over_adapter_type_and_other_authors_local_cards(monkeypatch) -> None:
    catalog = load_catalog()
    card = replace(catalog.models[0], provider="alpha", id="shared", display_name="Local Alpha")
    monkeypatch.setattr(catalog_module, "load_catalog", lambda: replace(catalog, models=(*catalog.models, card)))

    assert get_model_display_name("alpha", "shared") == "Local Alpha"
    assert get_model_display_name("alpha", "beta/shared") == "Beta: Shared"
    assert get_model_display_name("alpha", "gateway/beta/shared") == "Beta: Shared"
    assert get_model_display_name("private", "shared") == "shared"


@pytest.mark.usefixtures("name_overlays")
@pytest.mark.parametrize(
    ("provider", "model_id", "expected"),
    [
        ("private", "shared", "shared"),
        ("beta", "shared", "Beta: Shared"),
        ("alpha", "unknown/shared", "unknown/shared"),
        ("alpha", "beta/unique", "beta/unique"),
        ("openai", "alpha/shared:free", "Alpha: Shared (free)"),
        ("openai", "alpha/shared:nitro", "alpha/shared:nitro"),
        ("openai", "alpha/org/model", "Alpha: Nested Model"),
        ("openai", "~alpha/shared", "Alpha: Shared Router"),
        ("private", "custom-model", "custom-model"),
        ("openai", "", ""),
    ],
)
def test_names_do_not_conflate_authors_nested_slugs_or_variants(provider, model_id, expected) -> None:
    assert get_model_display_name(provider, model_id) == expected


@pytest.mark.usefixtures("name_overlays")
@pytest.mark.parametrize(
    ("provider", "model_id", "expected"),
    [
        ("moonshot", "kimi-example", "MoonshotAI: Kimi Example"),
        ("zhipu", "glm-example", "Z.ai: GLM Example"),
        ("openai", "zhipu/glm-example", "Z.ai: GLM Example"),
        ("openai", "anthropic/claude-example.1", "Anthropic: Claude Example 1"),
        ("anthropic", "claude-example-1", "claude-example-1"),
    ],
)
def test_author_aliases_are_explicit_and_model_punctuation_is_not_guessed(provider, model_id, expected) -> None:
    assert get_model_display_name(provider, model_id) == expected


@pytest.mark.usefixtures("name_overlays")
def test_lobehub_and_raw_ids_still_work_without_openrouter_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(catalog_module, "_load_openrouter_names", lambda: {})
    assert get_model_display_name("openai", "gateway/legacy/fallback") == "Legacy Name"
    assert get_model_display_name("private", "fallback") == "Legacy Name"
    assert get_model_display_name("private", "custom-model") == "custom-model"


@pytest.mark.usefixtures("name_overlays")
def test_external_names_never_create_capability_cards() -> None:
    catalog = load_catalog()
    assert get_model_display_name("alpha", "unique") == "Alpha: Unique"
    assert get_model("alpha", "unique") is None
    assert load_catalog() is catalog


def test_missing_optional_snapshot_loads_an_empty_overlay(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(catalog_module, "files", lambda _package: tmp_path)
    assert catalog_module._load_openrouter_names.__wrapped__() == {}
