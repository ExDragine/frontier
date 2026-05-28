"""测试桩：用于替代重量级第三方库的假实现。"""

import inspect
import types
from typing import get_args, get_origin


class DummyEmbeddings:
    def __init__(self, **_kwargs):
        pass

    def embed_documents(self, docs):
        return [[0.0] * 3 for _ in docs]

    def embed_query(self, text):
        return [0.0, 0.0, 0.0]


class DummyPersistentClient:
    def __init__(self, **_kwargs):
        pass


class DummyFilesystemBackend:
    def __init__(self, **kw):
        self.kwargs = kw
        self.root_dir = kw.get("root_dir")
        self.virtual_mode = kw.get("virtual_mode")


class DummyCompositeBackend:
    def __init__(self, default, routes, **kw):
        self.default = default
        self.routes = routes
        self.kwargs = kw
        self.artifacts_root = kw.get("artifacts_root", "/")


class DummyModel:
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


class DummyTokenizer:
    @classmethod
    def from_pretrained(cls, *_args, **_kwargs):
        return cls()

    def apply_chat_template(self, messages, tokenize=False):
        return ""

    def __call__(self, texts, return_tensors=None):
        return types.SimpleNamespace(input_ids=[[0]], to=lambda device: self)

    def decode(self, ids, skip_special_tokens=True):
        return "Safety: Safe"


class DummyScheduler:
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


class DummyContext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return None


def is_injected_tool_arg(annotation) -> bool:
    if get_origin(annotation) is not None:
        return any(is_injected_tool_arg(item) for item in get_args(annotation))
    return getattr(annotation, "__name__", "") == "InjectedState" or annotation.__class__.__name__ == "InjectedState"


def fake_tool(name_or_callable=None, *_args, **_kwargs):
    def decorate(func):
        signature = inspect.signature(func)
        func.name = name_or_callable if isinstance(name_or_callable, str) else func.__name__
        func.args = {
            name: {"title": name.replace("_", " ").title().replace(" ", ""), "type": "string"}
            for name, parameter in signature.parameters.items()
            if not is_injected_tool_arg(parameter.annotation)
        }
        return func

    if callable(name_or_callable):
        return decorate(name_or_callable)
    return decorate
