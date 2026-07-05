# ruff: noqa: S101

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

from .stubs.install import install_all_third_party_stubs

install_all_third_party_stubs()
_tools_dir = Path(__file__).resolve().parents[1] / "tools"


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

    plugin_load.require = lambda *_args, **_kwargs: None
    nonebot.require = plugin_load.require
    try:
        nonebot.init(**config.stash[NONEBOT_INIT_KWARGS])
    except Exception as exc:
        config.stash["nonebot_init_error"] = exc


def pytest_sessionstart(session):
    import nonebot
    import nonebot.plugin.load as plugin_load

    plugin_load.require = lambda *_args, **_kwargs: None
    nonebot.require = plugin_load.require


# Ensure repo root is importable during collection
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def _ensure_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_path = tmp_path / "env.toml"
    env_path.write_text(
        """
[information]
name = "FrontierBot"

[endpoint]
openai_base_url = "https://example.com"
basic_model = "gpt-4o-mini"
advan_model = "gpt-4"
paint_model = "gpt-4-vision"
basic_model_use_responses_api = true
advan_model_use_responses_api = true

[key]
openai_api_key = "sk-test"
nasa_api_key = "nasa-test"
github_pat = "ghp-test"
google_api_key = "ggl-test"
anthropic_api_key = "ant-test"
anthropic_base_url = ""

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "none"
agent_whitelist_mode = false
agent_whitelist_person_list = []
agent_whitelist_group_list = []
agent_blacklist_person_list = []
agent_blacklist_group_list = []
paint_whitelist_mode = false
paint_whitelist_person_list = []
paint_whitelist_group_list = []
paint_blacklist_person_list = []
paint_blacklist_group_list = []

[message]
test_group_id = []

[database]
query_message_numbers = 5

[debug]
agent_debug_mode = false

[memory]
enabled = true
schema_version = "v2"
auto_rebuild_on_startup = true
embedding_model = "mock-embed"
default_task_ttl_days = 7
max_injected_memories = 4
retrieval_user_k = 6
retrieval_group_k = 6
privacy_mode = "balanced"
inject_timeout_ms = 500

[dashboard]
password = "admin"
jwt_secret = "secret"
jwt_expire_hours = 1
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def load_tool_module():
    """Load a single tools/*.py module without triggering tools/__init__.py discovery."""
    tools_pkg = sys.modules.setdefault("tools", importlib.util.module_from_spec(importlib.machinery.ModuleSpec("tools", None)))
    tools_pkg.__path__ = [str(_tools_dir)]

    def _load(module_name: str):
        qualified_name = f"tools.{module_name}"
        module_path = _tools_dir / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(qualified_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load tool module {module_name!r} from {module_path}")
        sys.modules.pop(qualified_name, None)
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        setattr(tools_pkg, module_name, module)
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

    plugin_load.require = safe_require
    nonebot.require = safe_require
    if "utils.configs" in sys.modules:
        importlib.reload(sys.modules["utils.configs"])
    yield
    if "utils.configs" in sys.modules:
        importlib.reload(sys.modules["utils.configs"])
