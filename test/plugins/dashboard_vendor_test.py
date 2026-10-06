# ruff: noqa: S101

"""The Dashboard asset table, index.html and the vendoring script must agree."""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "vendor_dashboard_assets.py"
INDEX_HTML = REPO_ROOT / "plugins" / "dashboard" / "web" / "index.html"
_MODULE_NAME = "vendor_dashboard_assets_under_test"


def _load_script():
    cached = sys.modules.get(_MODULE_NAME)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before execution: dataclass creation resolves the defining module
    # through sys.modules.
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def test_index_html_references_every_pinned_asset():
    module = _load_script()
    html = INDEX_HTML.read_text(encoding="utf-8")
    for asset in module.assets():
        assert asset.local_source in html, f"{asset.local_source} is not loaded by index.html"
        assert asset.url in html, f"the pinned fallback {asset.url} is missing from index.html"


def test_vendor_directory_is_the_path_the_page_requests():
    module = _load_script()
    assert module.VENDOR_DIR == REPO_ROOT / "plugins" / "dashboard" / "web" / "vendor"
    assert module.INDEX_HTML == INDEX_HTML


def test_missing_assets_tracks_the_vendor_directory(tmp_path):
    module = _load_script()
    assert len(module.missing_assets(tmp_path)) == len(module.assets())
    for asset in module.assets():
        (tmp_path / asset.filename).write_bytes(b"pinned")
    assert module.missing_assets(tmp_path) == []


def test_check_mode_exit_code_follows_vendored_state(monkeypatch, tmp_path, capsys):
    module = _load_script()
    monkeypatch.setattr(module, "VENDOR_DIR", tmp_path)

    assert module.main(["--check"]) == 1
    assert "missing" in capsys.readouterr().err

    for asset in module.assets():
        (tmp_path / asset.filename).write_bytes(b"pinned")

    assert module.main(["--check"]) == 0
    assert "no CDN request" in capsys.readouterr().out
