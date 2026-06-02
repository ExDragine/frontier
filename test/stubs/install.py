"""模块桩安装器：在 sys.modules 中预置假模块，阻止真实第三方库导入。"""

import sys
import types

from .dummies import (
    DummyCompositeBackend,
    DummyContext,
    DummyEmbeddings,
    DummyFilesystemBackend,
    DummyLocalShellBackend,
    DummyModel,
    DummyPersistentClient,
    DummyScheduler,
    DummyTokenizer,
    fake_tool,
)


def install_stub(module_name: str, **attrs):
    """在 sys.modules 中安装假模块，阻止真实库被导入。"""
    module = types.ModuleType(module_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[module_name] = module
    if "." in module_name:
        parent, child = module_name.rsplit(".", 1)
        if parent not in sys.modules:
            install_stub(parent)
        setattr(sys.modules[parent], child, module)
    return module


def install_all_third_party_stubs():
    """安装所有必要的第三方库桩。"""
    install_stub("chromadb", PersistentClient=DummyPersistentClient)
    install_stub("uuid_utils", uuid7=lambda: "uuid")
    install_stub("langchain_huggingface", HuggingFaceEmbeddings=DummyEmbeddings)
    install_stub("deepagents", create_deep_agent=lambda **_kwargs: types.SimpleNamespace(ainvoke=lambda *a, **k: {}))
    install_stub(
        "deepagents.backends",
        CompositeBackend=DummyCompositeBackend,
        FilesystemBackend=DummyFilesystemBackend,
        LocalShellBackend=DummyLocalShellBackend,
    )
    install_stub(
        "langchain.agents",
        AgentState=type("AgentState", (), {}),
        create_agent=lambda **_kwargs: types.SimpleNamespace(ainvoke=lambda *a, **k: {}),
    )
    install_stub("langchain.tools", tool=fake_tool)
    install_stub(
        "langchain.agents.middleware",
        FilesystemFileSearchMiddleware=type(
            "FilesystemFileSearchMiddleware", (), {"__init__": lambda self, *_a, **_kw: None}
        ),
        ModelRetryMiddleware=type("ModelRetryMiddleware", (), {"__init__": lambda self, *_a, **_kw: None}),
        PIIMiddleware=type("PIIMiddleware", (), {"__init__": lambda self, *_a, **_kw: None}),
        ToolRetryMiddleware=type("ToolRetryMiddleware", (), {"__init__": lambda self, *_a, **_kw: None}),
    )
    install_stub(
        "langchain.messages",
        AIMessage=type("AIMessage", (), {"__init__": lambda self, content=None: setattr(self, "content", content)}),
    )
    install_stub("langchain_core.runnables", RunnableConfig=dict)
    install_stub("langchain_openai", ChatOpenAI=type("ChatOpenAI", (), {"__init__": lambda self, **_kw: None}))
    install_stub("langchain_deepseek", ChatDeepSeek=type("ChatDeepSeek", (), {"__init__": lambda self, **_kw: None}))
    install_stub(
        "langchain_anthropic",
        ChatAnthropic=type("ChatAnthropic", (), {"__init__": lambda self, **_kw: None}),
    )
    install_stub(
        "langchain_google_genai",
        ChatGoogleGenerativeAI=type("ChatGoogleGenerativeAI", (), {"__init__": lambda self, **_kw: None}),
    )
    install_stub("langgraph.checkpoint.memory", InMemorySaver=object)
    install_stub("langchain_community.document_loaders", BiliBiliLoader=object)
    install_stub("langchain_core.documents", Document=object)

    install_stub(
        "tools.agent_tools",
        all_tools=[],
        main_tools=[],
        core_tools=[],
        searchable_tools=[],
        web_tools=[],
        mcp_tools=[],
        tool_metadata={},
        subagent_tools={
            "research": [],
            "astro": [],
            "earth": [],
            "media": [],
            "memory": [],
            "divination": [],
            "external": [],
        },
    )

    install_stub("nonebot_plugin_apscheduler", scheduler=DummyScheduler())

    install_stub(
        "torch",
        inference_mode=lambda: DummyContext(),
        cuda=types.SimpleNamespace(is_available=lambda: False, get_device_name=lambda *_: ""),
    )
    install_stub(
        "torchao.quantization",
        Int8WeightOnlyConfig=type("Int8WeightOnlyConfig", (), {"__init__": lambda self, **_kw: None}),
        quantize_=lambda *_args, **_kwargs: None,
    )
    install_stub(
        "transformers",
        AutoModelForCausalLM=DummyModel,
        AutoModelForImageClassification=DummyModel,
        AutoTokenizer=DummyTokenizer,
        ViTImageProcessor=type(
            "ViTImageProcessor",
            (),
            {"from_pretrained": classmethod(lambda cls, *_a, **_k: cls()), "__call__": lambda self, **_k: {}},
        ),
    )
