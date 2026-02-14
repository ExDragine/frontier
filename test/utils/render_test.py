# ruff: noqa: S101

import types

import pytest

from utils import render


@pytest.mark.asyncio
async def test_playwright_render_eq_usgs(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "earthquake.html").write_text(
        "<html><body><div id='card'>ok</div></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "cache").mkdir()

    class DummyPage:
        async def goto(self, *_args, **_kwargs):
            return None

        async def wait_for_load_state(self, *_args, **_kwargs):
            return None

        async def wait_for_timeout(self, *_args, **_kwargs):
            return None

        async def query_selector(self, *_args, **_kwargs):
            async def screenshot(**_kw):
                return b"img"

            return types.SimpleNamespace(screenshot=screenshot)

    class DummyBrowser:
        async def new_page(self):
            return DummyPage()

        async def close(self):
            return None

    class DummyPlaywright:
        async def __aenter__(self):
            async def launch():
                return DummyBrowser()

            self.chromium = types.SimpleNamespace(launch=launch)
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def fake_async_playwright():
        return DummyPlaywright()

    monkeypatch.setattr(render, "async_playwright", fake_async_playwright)

    payload = {
        "title": "Earthquake",
        "detail": [],
        "latitude": 0,
        "longitude": 0,
        "magnitude": 1,
        "depth": 10,
    }
    result = await render.playwright_render("eq_usgs", payload)
    assert result == b"img"


@pytest.mark.asyncio
async def test_playwright_render_eq_cenc_with_depth_units(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "earthquake.html").write_text(
        "<html><body><div id='card'>ok</div></body></html>",
        encoding="utf-8",
    )
    (tmp_path / "cache").mkdir()

    class DummyPage:
        async def goto(self, *_args, **_kwargs):
            return None

        async def wait_for_load_state(self, *_args, **_kwargs):
            return None

        async def wait_for_timeout(self, *_args, **_kwargs):
            return None

        async def query_selector(self, *_args, **_kwargs):
            async def screenshot(**_kw):
                return b"img"

            return types.SimpleNamespace(screenshot=screenshot)

    class DummyBrowser:
        async def new_page(self):
            return DummyPage()

        async def close(self):
            return None

    class DummyPlaywright:
        async def __aenter__(self):
            async def launch():
                return DummyBrowser()

            self.chromium = types.SimpleNamespace(launch=launch)
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def fake_async_playwright():
        return DummyPlaywright()

    monkeypatch.setattr(render, "async_playwright", fake_async_playwright)

    payload = {
        "title": "Earthquake",
        "detail": [],
        "latitude": 0,
        "longitude": 0,
        "magnitude": 1,
        "depth": "10千米",
    }
    result = await render.playwright_render("eq_cenc", payload)
    assert result == b"img"
