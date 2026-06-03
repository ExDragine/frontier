# ruff: noqa: S101

from pathlib import Path

import pytest

from policy.errors import PolicyLoadError
from policy.manifesto import Manifesto


class TestManifestoLoad:
    def test_load_valid_manifesto(self, manifesto_file: Path):
        manifesto = Manifesto.from_yaml(manifesto_file)
        assert manifesto.version == "1.0"
        assert manifesto.metadata.name == "test-policy"
        assert "input" in manifesto.intervention_points
        assert len(manifesto.intervention_points["input"]) == 2

    def test_load_missing_file_raises(self, tmp_path: Path):
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            Manifesto.from_yaml(missing)

    def test_load_invalid_yaml_raises_policy_load_error(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(": : : :", encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="Invalid YAML"):
            Manifesto.from_yaml(bad)

    def test_load_non_mapping_raises_policy_load_error(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("- just a list", encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="must be a YAML mapping"):
            Manifesto.from_yaml(bad)

    def test_load_missing_required_fields_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text('version: "1.0"\n', encoding="utf-8")
        with pytest.raises(PolicyLoadError, match="Invalid manifesto schema"):
            Manifesto.from_yaml(bad)
