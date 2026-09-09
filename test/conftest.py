# ruff: noqa: S101

import importlib
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest

from .stubs.install import install_all_third_party_stubs

install_all_third_party_stubs()
os.environ.setdefault("NICKNAME", '["FrontierBot"]')
_tools_dir = Path(__file__).resolve().parents[1] / "tools"
_collection_env = pytest.StashKey[tuple[pytest.MonkeyPatch, tempfile.TemporaryDirectory]]()


def pytest_configure(config):
    try:
        from nonebug import NONEBOT_INIT_KWARGS
    except Exception:
        return

    config.stash.setdefault(
        NONEBOT_INIT_KWARGS,
        {
            "driver": "nonebot.drivers.fastapi:Driver",
            "log_level": "WARNING",
        },
    )

    config.stash[NONEBOT_INIT_KWARGS]["driver"] = "nonebot.drivers.fastapi:Driver"
    try:
        from nonebug import NONEBOT_START_LIFESPAN
    except Exception as exc:
        config.stash["nonebug_start_lifespan_import_error"] = exc
    else:
        config.stash[NONEBOT_START_LIFESPAN] = False

    import nonebot
    import nonebot.plugin.load as plugin_load

    plugin_load.__dict__["require"] = lambda *_args, **_kwargs: None
    nonebot.__dict__["require"] = plugin_load.require
    try:
        nonebot.init(**config.stash[NONEBOT_INIT_KWARGS])
    except Exception as exc:
        config.stash["nonebot_init_error"] = exc


def pytest_sessionstart(session):
    # Collection imports application modules before per-test fixtures run.
    # Keep their config/database/cache initialization outside the real workspace.
    temporary_dir = tempfile.TemporaryDirectory(prefix="frontier-test-collection-")
    monkeypatch = pytest.MonkeyPatch()
    session.config.stash[_collection_env] = monkeypatch, temporary_dir
    monkeypatch.delenv("FRONTIER_CONFIG", raising=False)
    _ensure_env_file(monkeypatch, Path(temporary_dir.name))

    import nonebot
    import nonebot.plugin.load as plugin_load

    plugin_load.__dict__["require"] = lambda *_args, **_kwargs: None
    nonebot.__dict__["require"] = plugin_load.require


def pytest_sessionfinish(session):
    monkeypatch, temporary_dir = session.config.stash[_collection_env]
    monkeypatch.undo()
    temporary_dir.cleanup()


# Ensure repo root is importable during collection
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def _ensure_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("NICKNAME", '["FrontierBot"]')
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
config_version = 2

[models]
basic_model = "gpt-4o-mini"
advanced_model = "gpt-4"
paint_model = "gpt-4-vision"

[providers.openai]
type = "openai"
api_mode = "responses"
base_url = "https://example.com"
api_key = "sk-test"

[providers.google]
type = "google"
api_key = "ggl-test"

[providers.anthropic]
type = "anthropic"
api_key = "ant-test"

[key]
nasa_api_key = "nasa-test"
github_pat = "ghp-test"

[agent]
reasoning_effort = "none"

[storage]
query_message_numbers = 5

[dashboard]
password = "admin"
jwt_secret = "frontier-test-jwt-secret-at-least-32-bytes"
jwt_expire_hours = 1

""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def load_tool_module(monkeypatch: pytest.MonkeyPatch):
    """Load a single tools/*.py module without triggering tools/__init__.py discovery."""
    tools_pkg = sys.modules.get("tools")
    if tools_pkg is None:
        tools_pkg = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("tools", None))
        monkeypatch.setitem(sys.modules, "tools", tools_pkg)
    monkeypatch.setattr(tools_pkg, "__path__", [str(_tools_dir)], raising=False)

    def _load(module_name: str):
        qualified_name = f"tools.{module_name}"
        module_path = _tools_dir / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(qualified_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load tool module {module_name!r} from {module_path}")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, qualified_name, module)
        monkeypatch.setattr(tools_pkg, module_name, module, raising=False)
        spec.loader.exec_module(module)
        return module

    return _load


@pytest.fixture(autouse=True)
def reset_env_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _ensure_env_file(monkeypatch, tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    import nonebot
    import nonebot.plugin.load as plugin_load

    def safe_require(name, *_args, **_kwargs):
        if name == "nonebot_plugin_apscheduler":
            return None
        return plugin_load.load_plugin(name)

    monkeypatch.setattr(plugin_load, "require", safe_require)
    monkeypatch.setattr(nonebot, "require", safe_require)
    if "utils.configs" in sys.modules:
        importlib.reload(sys.modules["utils.configs"])
    yield
    if "utils.configs" in sys.modules:
        importlib.reload(sys.modules["utils.configs"])
