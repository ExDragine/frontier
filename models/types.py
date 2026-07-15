from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelStatus(StrEnum):
    ACTIVE = "active"
    PREVIEW = "preview"
    LEGACY = "legacy"
    DEPRECATED = "deprecated"


class ModelInput(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"


class ModelOutput(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ModelFeature(StrEnum):
    REASONING = "reasoning"
    TOOL_CALLING = "tool_calling"
    PARALLEL_TOOL_CALLING = "parallel_tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    WEB_SEARCH = "web_search"
    IMAGE_GENERATION = "image_generation"


class ApiMode(StrEnum):
    CHAT_COMPLETIONS = "chat_completions"
    RESPONSES = "responses"
    MESSAGES = "messages"
    GENERATE_CONTENT = "generate_content"


@dataclass(frozen=True, slots=True)
class LocalizedDescription:
    en: str
    zh_cn: str


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    input: tuple[ModelInput, ...]
    output: tuple[ModelOutput, ...]
    features: tuple[ModelFeature, ...]
    api_modes: tuple[ApiMode, ...]


@dataclass(frozen=True, slots=True)
class ModelSource:
    url: str
    verified_at: str


@dataclass(frozen=True, slots=True)
class ModelCard:
    provider: str
    id: str
    display_name: str
    description: LocalizedDescription
    capabilities: ModelCapabilities
    context_window: int | None
    max_output_tokens: int | None
    knowledge_cutoff: str | None
    released_at: str | None
    status: ModelStatus
    sources: tuple[ModelSource, ...]


@dataclass(frozen=True, slots=True)
class ModelCatalog:
    schema_version: str
    catalog_version: str
    updated_at: str
    models: tuple[ModelCard, ...]
