# ruff: noqa: S101

from pathlib import Path

import pytest

# ── is_local ──────────────────────────────────────────────────────────────────


def test_is_local_finds_file_with_root_dir(tmp_path):
    from utils.milky_tools import is_local

    (tmp_path / "report.pdf").write_text("pdf")

    assert is_local("/report.pdf", root_dir=str(tmp_path)) is True


def test_is_local_finds_file_with_relative_path(tmp_path, monkeypatch):
    from utils.milky_tools import is_local

    (tmp_path / "a.txt").write_text("hello")
    monkeypatch.chdir(tmp_path)

    assert is_local("a.txt") is True


def test_is_local_returns_false_when_not_found(tmp_path):
    from utils.milky_tools import is_local

    assert is_local("/nope.txt", root_dir=str(tmp_path)) is False


def test_is_local_rejects_absolute_path_without_root_dir(tmp_path):
    from utils.milky_tools import is_local

    f = tmp_path / "a.txt"
    f.write_text("hello")

    # Absolute paths are NOT allowed without a root_dir sandbox
    assert is_local(str(f)) is False


def test_is_local_blocks_path_traversal(tmp_path):
    from utils.milky_tools import is_local

    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "legal.txt").write_text("ok")
    (tmp_path / "secret.txt").write_text("secret")

    assert is_local("/legal.txt", root_dir=str(root)) is True
    assert is_local("../secret.txt", root_dir=str(root)) is False
    assert is_local("../../secret.txt", root_dir=str(root)) is False


# ── resolve_local_path ───────────────────────────────────────────────────────


def test_resolve_local_path_resolves_against_root_dir(tmp_path):
    from utils.milky_tools import resolve_local_path

    (tmp_path / "report.pdf").write_text("pdf")

    result = resolve_local_path("/report.pdf", root_dir=str(tmp_path))
    assert result == (tmp_path / "report.pdf").resolve()


def test_resolve_local_path_resolves_relative_path(tmp_path, monkeypatch):
    from utils.milky_tools import resolve_local_path

    (tmp_path / "report.pdf").write_text("pdf")
    monkeypatch.chdir(tmp_path)

    result = resolve_local_path("report.pdf")
    assert result == (tmp_path / "report.pdf").resolve()


def test_resolve_local_path_returns_none_when_not_found(tmp_path):
    from utils.milky_tools import resolve_local_path

    assert resolve_local_path("/nope.txt", root_dir=str(tmp_path)) is None


def test_resolve_local_path_blocks_path_traversal(tmp_path):
    from utils.milky_tools import resolve_local_path

    root = tmp_path / "sandbox"
    root.mkdir()
    (root / "legal.txt").write_text("ok")
    (tmp_path / "secret.txt").write_text("secret")

    assert resolve_local_path("/legal.txt", root_dir=str(root)) is not None
    assert resolve_local_path("../secret.txt", root_dir=str(root)) is None
    assert resolve_local_path("../../etc/passwd", root_dir=str(root)) is None


def test_resolve_local_path_rejects_absolute_path_without_root_dir(tmp_path):
    from utils.milky_tools import resolve_local_path

    f = tmp_path / "real.txt"
    f.write_text("real")

    assert resolve_local_path(str(f)) is None


def test_resolve_local_path_root_dir_takes_priority_over_absolute_path(tmp_path):
    from utils.milky_tools import resolve_local_path

    # File outside the sandbox — must NOT be accessible when root_dir is set
    real_file = tmp_path / "real.txt"
    real_file.write_text("real")

    sandbox = tmp_path / "shadow"
    sandbox.mkdir()

    # When root_dir is provided, the path is always resolved inside the sandbox.
    # An absolute path outside the sandbox does NOT exist inside, so return None.
    result = resolve_local_path(str(real_file), root_dir=str(sandbox))
    assert result is None

    # Only files within the sandbox are accessible
    (sandbox / "real.txt").write_text("shadow")
    result = resolve_local_path("/real.txt", root_dir=str(sandbox))
    assert result == (sandbox / "real.txt").resolve()
    assert result.read_text() == "shadow"


# ── binary_kwargs_from_uri ───────────────────────────────────────────────────


def test_binary_kwargs_from_uri_resolves_local_file(tmp_path, monkeypatch):
    from utils.milky_tools import binary_kwargs_from_uri

    (tmp_path / "a.txt").write_text("hello")
    monkeypatch.chdir(tmp_path)

    assert binary_kwargs_from_uri("a.txt") == {"path": str(Path("a.txt").resolve())}


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
