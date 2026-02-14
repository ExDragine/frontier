# ruff: noqa: S101

import importlib
import sys
from pathlib import Path
import types

import pytest


def _install_stub(module_name: str, **attrs):
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module
    if "." in module_name:
        parent, child = module_name.rsplit(".", 1)
        if parent not in sys.modules:
            _install_stub(parent)
        setattr(sys.modules[parent], child, module)
    return module


class _DummyEmbeddings:
    def __init__(self, **_kwargs):
        pass

    def embed_documents(self, docs):
        return [[0.0] * 3 for _ in docs]

    def embed_query(self, text):
        return [0.0, 0.0, 0.0]


class _DummyPersistentClient:
    def __init__(self, **_kwargs):
        pass


class _DummyModel:
    device = "cpu"

    @classmethod
    def from_pretrained(cls, *_args, **_kwargs):
        return cls()

    def eval(self):
        return self

    def generate(self, **_kwargs):
        return [[0]]

    def __call__(self, **_kwargs):
        return types.SimpleNamespace(
            logits=types.SimpleNamespace(argmax=lambda *_: types.SimpleNamespace(item=lambda: 0))
        )


class _DummyTokenizer:
    @classmethod
    def from_pretrained(cls, *_args, **_kwargs):
        return cls()

    def apply_chat_template(self, messages, tokenize=False):
        return ""

    def __call__(self, texts, return_tensors=None):
        return types.SimpleNamespace(input_ids=[[0]], to=lambda device: self)

    def decode(self, ids, skip_special_tokens=True):
        return "Safety: Safe"


def _install_third_party_stubs():
    _install_stub("chromadb", PersistentClient=_DummyPersistentClient)
    _install_stub("uuid_utils", uuid7=lambda: "uuid")
    _install_stub("langchain_huggingface", HuggingFaceEmbeddings=_DummyEmbeddings)
    _install_stub("deepagents", create_deep_agent=lambda **_kwargs: types.SimpleNamespace(ainvoke=lambda *a, **k: {}))
    _install_stub(
        "deepagents.backends", FilesystemBackend=type("FilesystemBackend", (), {"__init__": lambda self, **_kw: None})
    )
    _install_stub(
        "langchain.agents",
        AgentState=type("AgentState", (), {}),
        create_agent=lambda **_kwargs: types.SimpleNamespace(ainvoke=lambda *a, **k: {}),
    )
    _install_stub("langchain.tools", tool=lambda func=None, **_kwargs: func if func else (lambda f: f))
    _install_stub("langchain.agents.middleware", PIIMiddleware=object)
    _install_stub(
        "langchain.messages",
        AIMessage=type("AIMessage", (), {"__init__": lambda self, content=None: setattr(self, "content", content)}),
    )
    _install_stub("langchain_core.runnables", RunnableConfig=dict)
    _install_stub("langchain_openai", ChatOpenAI=type("ChatOpenAI", (), {"__init__": lambda self, **_kw: None}))
    _install_stub(
        "langchain_anthropic",
        ChatAnthropic=type("ChatAnthropic", (), {"__init__": lambda self, **_kw: None}),
    )
    _install_stub(
        "langchain_google_genai",
        ChatGoogleGenerativeAI=type("ChatGoogleGenerativeAI", (), {"__init__": lambda self, **_kw: None}),
    )
    _install_stub("langgraph.checkpoint.memory", InMemorySaver=object)

    _install_stub("langchain_community.document_loaders", BiliBiliLoader=object)
    _install_stub("langchain_core.documents", Document=object)

    _install_stub(
        "tools.agent_tools",
        all_tools=[],
        web_tools=[],
        mcp_tools=[],
    )

    class _DummyScheduler:
        def add_listener(self, *_args, **_kwargs):
            return None

        def add_job(self, *_args, **_kwargs):
            return None

        def pause_job(self, *_args, **_kwargs):
            return None

        def reschedule_job(self, *_args, **_kwargs):
            return None

        def remove_job(self, *_args, **_kwargs):
            return None

        def get_job(self, *_args, **_kwargs):
            return types.SimpleNamespace(next_run_time=None)

    _install_stub("nonebot_plugin_apscheduler", scheduler=_DummyScheduler())

    class _DummyContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return None

    _install_stub(
        "torch",
        inference_mode=lambda: _DummyContext(),
        cuda=types.SimpleNamespace(is_available=lambda: False, get_device_name=lambda *_: ""),
    )
    _install_stub(
        "torchao.quantization",
        Int8WeightOnlyConfig=type("Int8WeightOnlyConfig", (), {"__init__": lambda self, **_kw: None}),
        quantize_=lambda *_args, **_kwargs: None,
    )
    _install_stub(
        "transformers",
        AutoModelForCausalLM=_DummyModel,
        AutoModelForImageClassification=_DummyModel,
        AutoTokenizer=_DummyTokenizer,
        ViTImageProcessor=type(
            "ViTImageProcessor",
            (),
            {"from_pretrained": classmethod(lambda cls, *_a, **_k: cls()), "__call__": lambda self, **_k: {}},
        ),
    )


_install_third_party_stubs()


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
    except Exception:
        pass
    else:
        config.stash[NONEBOT_START_LIFESPAN] = False

    import nonebot
    import nonebot.plugin.load as plugin_load

    plugin_load.require = lambda *_args, **_kwargs: None
    nonebot.require = plugin_load.require
    try:
        nonebot.init(**config.stash[NONEBOT_INIT_KWARGS])
    except Exception:
        pass


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
basic_model = "basic"
advan_model = "advan"
paint_model = "paint"

[key]
openai_api_key = "sk-test"
nasa_api_key = "nasa-test"
github_pat = "ghp-test"

[function]
agent_module_enabled = true
paint_module_enabled = true
agent_capability = "minimal"
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
raw_message_group_id = []
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
