# ruff: noqa: S101

import types

import pytest

from plugins.watchtower import environment_check


def test_cpu_check_fallback(monkeypatch):
    monkeypatch.setattr(environment_check, "platform", types.SimpleNamespace(processor=lambda: "Intel"))
    monkeypatch.setattr(environment_check, "sys", types.SimpleNamespace(platform="linux"))
    import builtins

    original_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if str(path).endswith("/proc/cpuinfo"):
            raise FileNotFoundError()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    assert environment_check.cpu_check() in {"intel", "amd", "unknown"}


def test_gpu_check_no_torch(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert environment_check.gpu_check() in {None, "none"}


def test_system_check_toml(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cache").mkdir()

    class DummyTomlkit:
        def load(self, *_args, **_kwargs):
            return {}

        def dump(self, data, fp):
            fp.write("[hardware]\n")

    import sys

    sys.modules["tomlkit"] = DummyTomlkit()
    environment_check.system_check()
