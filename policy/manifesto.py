"""YAML manifesto 解析与校验。"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .errors import PolicyLoadError


class PolicyDefinition(BaseModel):
    type: str = "builtin"
    class_path: str
    description: str = ""


class PolicyBinding(BaseModel):
    policy: str
    config: dict[str, Any] = {}
    default_decision: str = "allow"


class ManifestoMetadata(BaseModel):
    name: str
    description: str = ""


class Manifesto(BaseModel):
    version: str
    metadata: ManifestoMetadata
    policies: dict[str, PolicyDefinition]
    intervention_points: dict[str, list[PolicyBinding]]

    @classmethod
    def from_yaml(cls, path: Path) -> "Manifesto":
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PolicyLoadError(f"Invalid YAML in manifesto {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise PolicyLoadError(f"Manifesto {path} must be a YAML mapping, got {type(raw).__name__}")
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            raise PolicyLoadError(f"Invalid manifesto schema in {path}:\n{exc}") from exc
