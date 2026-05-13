# ruff: noqa: S101

from pathlib import Path


def test_run_sh_sets_default_hf_endpoint_before_startup_work():
    script_path = Path(__file__).resolve().parents[1] / "run.sh"
    content = script_path.read_text(encoding="utf-8")

    export_line = 'export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"'

    assert export_line in content
    assert content.index(export_line) < content.index("uv sync")


def test_run_ps1_sets_default_hf_endpoint_without_overwriting_existing_value():
    script_path = Path(__file__).resolve().parents[1] / "run.ps1"
    content = script_path.read_text(encoding="utf-8")

    guard_line = "if (-not $env:HF_ENDPOINT)"
    assignment_line = '$env:HF_ENDPOINT = "https://hf-mirror.com"'

    assert guard_line in content
    assert assignment_line in content
    assert content.index(guard_line) < content.index("uv sync")
