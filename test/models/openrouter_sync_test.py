from __future__ import annotations

# ruff: noqa: S101
import hashlib
import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts import sync_openrouter_model_names as sync_module


def _response(*entries: dict, **extra) -> bytes:
    return json.dumps({"data": list(entries), **extra}).encode()


def test_build_snapshot_preserves_full_ids_variants_and_upstream_names() -> None:
    response = _response(
        {"id": "z-ai/GLM-example:free", "name": "Z.ai: GLM Example (free)", "context_length": 123},
        {"id": "alpha/example", "name": "Alpha: Example"},
        {"id": "alpha/org/model", "name": "Nested Model"},
        {"id": "~alpha/example-latest", "name": "Alpha: Example Latest"},
        links={"next": None},
    )
    snapshot = sync_module.build_snapshot(response)

    assert list(snapshot["models"]) == [
        "alpha/example",
        "alpha/org/model",
        "z-ai/glm-example:free",
        "~alpha/example-latest",
    ]
    assert snapshot["models"]["z-ai/glm-example:free"] == "Z.ai: GLM Example (free)"
    assert snapshot["model_count"] == 4
    assert snapshot["source"]["response_sha256"] == hashlib.sha256(response).hexdigest()
    assert "context_length" not in json.dumps(snapshot)
    schema_path = sync_module.DEFAULT_OUTPUT.with_suffix(".schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(snapshot)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"data": []},
        {"data": [None]},
        {"data": [{"id": "unqualified", "name": "Name"}]},
        {"data": [{"id": "alpha/", "name": "Name"}]},
        {"data": [{"id": "alpha/space here", "name": "Name"}]},
        {"data": [{"id": "alpha/example", "name": " "}]},
        {"data": [{"id": "alpha/example", "name": 42}]},
        {"data": [{"id": "alpha/example", "name": "Name"}], "links": {"next": "/next-page"}},
        {"data": [{"id": "alpha/example", "name": "Name"}], "links": []},
    ],
)
def test_build_snapshot_rejects_invalid_or_partial_responses(payload) -> None:
    with pytest.raises(ValueError):
        sync_module.build_snapshot(json.dumps(payload).encode())


def test_build_snapshot_rejects_conflicting_or_duplicate_case_insensitive_ids() -> None:
    with pytest.raises(ValueError, match="duplicate model ID"):
        sync_module.build_snapshot(
            _response({"id": "alpha/example", "name": "One"}, {"id": "alpha/EXAMPLE", "name": "Two"})
        )


def test_sync_ignores_price_order_and_provenance_changes_when_names_are_unchanged(monkeypatch, tmp_path) -> None:
    output = tmp_path / "names.json"
    entry = {"id": "alpha/example", "name": "Example", "pricing": {"prompt": "1"}}
    other = {"id": "beta/other", "name": "Other"}
    monkeypatch.setattr(sync_module, "_request_bytes", lambda: _response(entry, other))
    assert sync_module.sync(output=output, check=False)
    original = output.read_bytes()

    entry["pricing"]["prompt"] = "2"
    monkeypatch.setattr(sync_module, "_request_bytes", lambda: _response(other, entry))
    assert sync_module.sync(output=output, check=True)
    assert sync_module.sync(output=output, check=False)
    assert output.read_bytes() == original


def test_check_detects_new_names_and_missing_snapshots_without_writing(monkeypatch, tmp_path) -> None:
    output = tmp_path / "names.json"
    monkeypatch.setattr(sync_module, "_request_bytes", lambda: _response({"id": "alpha/example", "name": "Old"}))
    assert not sync_module.sync(output=output, check=True)
    assert not output.exists()
    assert sync_module.sync(output=output, check=False)
    original = output.read_bytes()

    monkeypatch.setattr(sync_module, "_request_bytes", lambda: _response({"id": "alpha/example", "name": "New"}))
    assert not sync_module.sync(output=output, check=True)
    assert output.read_bytes() == original
    assert sync_module.sync(output=output, check=False)
    assert json.loads(output.read_text(encoding="utf-8"))["models"] == {"alpha/example": "New"}


@pytest.mark.parametrize("response", [b"not JSON", b'{"data": []}'])
def test_invalid_download_preserves_existing_snapshot(monkeypatch, tmp_path, response) -> None:
    output = tmp_path / "names.json"
    output.write_text("existing snapshot", encoding="utf-8")
    monkeypatch.setattr(sync_module, "_request_bytes", lambda: response)
    with pytest.raises(ValueError):
        sync_module.sync(output=output, check=False)
    assert output.read_text(encoding="utf-8") == "existing snapshot"


def test_failed_atomic_replace_preserves_snapshot_and_cleans_temporary_file(monkeypatch, tmp_path) -> None:
    output = tmp_path / "names.json"
    output.write_text("existing snapshot", encoding="utf-8")
    original_files = set(tmp_path.iterdir())

    def fail_replace(*_args):
        raise OSError("replace failed")

    monkeypatch.setattr(sync_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        sync_module._write_atomic(output, "new snapshot")
    assert output.read_text(encoding="utf-8") == "existing snapshot"
    assert set(tmp_path.iterdir()) == original_files


def test_cli_reports_download_failure_and_preserves_snapshot(monkeypatch, tmp_path, capsys) -> None:
    output = tmp_path / "names.json"
    output.write_text("existing snapshot", encoding="utf-8")

    def offline():
        raise sync_module.httpx2.ConnectError("offline")

    monkeypatch.setattr(sync_module, "_request_bytes", offline)
    monkeypatch.setattr(sync_module.sys, "argv", ["sync", "--output", str(output)])
    assert sync_module.main() == 1
    assert "sync failed" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "existing snapshot"


def test_cli_imports_a_saved_response_without_network_access(monkeypatch, tmp_path) -> None:
    response_file = tmp_path / "response.json"
    response_file.write_bytes(_response({"id": "alpha/example", "name": "Example"}))
    output = tmp_path / "names.json"

    def no_network():
        pytest.fail("saved responses must not access the network")

    monkeypatch.setattr(sync_module, "_request_bytes", no_network)
    monkeypatch.setattr(sync_module.sys, "argv", ["sync", "--input", str(response_file), "--output", str(output)])
    assert sync_module.main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["models"] == {"alpha/example": "Example"}
