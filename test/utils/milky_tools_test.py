# ruff: noqa: S101

from pathlib import Path

import pytest


# ── is_local ──────────────────────────────────────────────────────────────────


def test_is_local_finds_file_on_real_filesystem(tmp_path):
    from utils.milky_tools import is_local

    f = tmp_path / "a.txt"
    f.write_text("hello")

    assert is_local(str(f)) is True


def test_is_local_finds_file_in_root_dir(tmp_path):
    from utils.milky_tools import is_local

    (tmp_path / "report.pdf").write_text("pdf")

    assert is_local(str(tmp_path / "report.pdf")) is True
    assert is_local("/report.pdf", root_dir=str(tmp_path)) is True


def test_is_local_returns_false_when_not_found(tmp_path):
    from utils.milky_tools import is_local

    assert is_local("/nope.txt") is False
    assert is_local("/nope.txt", root_dir=str(tmp_path)) is False


# ── resolve_local_path ───────────────────────────────────────────────────────


def test_resolve_local_path_returns_real_path_for_existing_file(tmp_path):
    from utils.milky_tools import resolve_local_path

    f = tmp_path / "a.txt"
    f.write_text("hello")

    result = resolve_local_path(str(f))
    assert result == f


def test_resolve_local_path_resolves_against_root_dir(tmp_path):
    from utils.milky_tools import resolve_local_path

    (tmp_path / "report.pdf").write_text("pdf")

    result = resolve_local_path("/report.pdf", root_dir=str(tmp_path))
    assert result == tmp_path / "report.pdf"


def test_resolve_local_path_returns_none_when_not_found(tmp_path):
    from utils.milky_tools import resolve_local_path

    assert resolve_local_path("/nope.txt") is None
    assert resolve_local_path("/nope.txt", root_dir=str(tmp_path)) is None


def test_resolve_local_path_prefers_real_filesystem_over_root_dir(tmp_path):
    from utils.milky_tools import resolve_local_path

    real_file = tmp_path / "real.txt"
    real_file.write_text("real")
    (tmp_path / "shadow").mkdir()
    (tmp_path / "shadow" / "real.txt").write_text("shadow")

    result = resolve_local_path(str(real_file), root_dir=str(tmp_path / "shadow"))
    assert result == real_file


# ── binary_kwargs_from_uri ───────────────────────────────────────────────────


def test_binary_kwargs_from_uri_resolves_local_file(tmp_path):
    from utils.milky_tools import binary_kwargs_from_uri

    f = tmp_path / "a.txt"
    f.write_text("hello")

    assert binary_kwargs_from_uri(str(f)) == {"path": str(f)}


def test_binary_kwargs_from_uri_resolves_from_root_dir(tmp_path):
    from utils.milky_tools import binary_kwargs_from_uri

    (tmp_path / "report.pdf").write_text("pdf")

    result = binary_kwargs_from_uri("/report.pdf", root_dir=str(tmp_path))
    assert result == {"path": str(tmp_path / "report.pdf")}


def test_binary_kwargs_from_uri_raises_for_unresolvable_path():
    from utils.milky_tools import binary_kwargs_from_uri

    with pytest.raises(ValueError, match="无效的文件 URI"):
        binary_kwargs_from_uri("/nope.pdf")


def test_binary_kwargs_from_uri_handles_http_url():
    from utils.milky_tools import binary_kwargs_from_uri

    result = binary_kwargs_from_uri("https://example.com/a.png")
    assert result == {"url": "https://example.com/a.png"}


def test_binary_kwargs_from_uri_handles_file_scheme(tmp_path):
    from utils.milky_tools import binary_kwargs_from_uri

    f = tmp_path / "data.bin"
    f.write_text("data")

    result = binary_kwargs_from_uri(f"file://{f}")
    assert result == {"path": str(f)}


def test_binary_kwargs_from_uri_handles_base64():
    from utils.milky_tools import binary_kwargs_from_uri

    result = binary_kwargs_from_uri("base64://aGVsbG8=")
    assert result == {"base64": "aGVsbG8="}


def test_binary_kwargs_from_uri_returns_empty_for_none():
    from utils.milky_tools import binary_kwargs_from_uri

    assert binary_kwargs_from_uri(None) == {}
    assert binary_kwargs_from_uri("") == {}
    assert binary_kwargs_from_uri("  ") == {}
