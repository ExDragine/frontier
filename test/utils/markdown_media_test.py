# ruff: noqa: S101
import io
import json
import socket
from types import SimpleNamespace

import httpx2
import pytest
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError

from utils import markdown_media as media
from utils.markdown_rich import UIBlock


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (640, 320), "#60a5fa").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "224.0.0.1", "::ffff:8.8.8.8"])
async def test_public_address_rejects_internal_and_multicast(monkeypatch, ip):
    async def dns(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]

    monkeypatch.setattr(media.asyncio.get_running_loop(), "getaddrinfo", dns)
    with pytest.raises(ValueError):
        await media.public_address("https://public.example/x")


@pytest.mark.asyncio
async def test_fetch_pins_dns_preserves_tls_and_rechecks_redirect(monkeypatch, tmp_path):
    seen = []

    async def address(url):
        if "internal" in url:
            raise ValueError("private")
        return "8.8.8.8", "public.example"

    monkeypatch.setattr(media, "public_address", address)

    def handler(request):
        seen.append(request)
        return httpx2.Response(302, headers={"location": "http://internal.example/secret"})

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        with pytest.raises(ValueError):
            await media.PublicFetcher(client, tmp_path).get("https://public.example/image.png")
    assert len(seen) == 1
    assert seen[0].url.host == "8.8.8.8"
    assert seen[0].headers["host"] == "public.example"
    assert seen[0].extensions["sni_hostname"] == "public.example"
    assert "cookie" not in seen[0].headers


@pytest.mark.asyncio
async def test_fetch_rejects_oversize_content(monkeypatch, tmp_path):
    async def address(url):
        return "8.8.8.8", "public.example"

    monkeypatch.setattr(media, "public_address", address)
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda r: httpx2.Response(200, stream=httpx2.ByteStream(b"12345")))
    ) as client:
        with pytest.raises(ValueError):
            await media.PublicFetcher(client, tmp_path).get("https://public.example/x", limit=4)


@pytest.mark.asyncio
async def test_media_route_aborts_writes_and_local_files(monkeypatch, tmp_path):
    class Route:
        request = SimpleNamespace(method="POST", resource_type="document", url="https://example.com")
        aborted = False

        async def abort(self):
            self.aborted = True

    async with httpx2.AsyncClient(trust_env=False) as client:
        route = Route()
        await media.PublicFetcher(client, tmp_path).route(route)
        assert route.aborted


def test_raster_reencodes_and_rejects_active_svg():
    data, width, height = media.raster_data(png())
    assert data.startswith("data:image/png;base64,") and (width, height) == (640, 320)
    with pytest.raises(UnidentifiedImageError):
        media.raster_data(b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')


@pytest.mark.asyncio
async def test_prepare_media_limits_loading_and_preserves_failure_fallback(monkeypatch, tmp_path):
    calls = []

    async def load(node, *args):
        calls.append(node["url"])
        node["media_error"] = "failed"

    monkeypatch.setattr(media, "load_media", load)
    config = {"children": [{"type": "image", "url": f"https://example.com/{i}", "alt": "demo"} for i in range(8)]}
    soup = BeautifulSoup('<div data-rich-kind="ui"></div>', "html.parser")
    soup.div["data-rich-config"] = json.dumps(config)
    result = await media.prepare_media(str(soup), None, width=1000, cache_dir=tmp_path)
    result_config = json.loads(BeautifulSoup(result, "html.parser").div["data-rich-config"])
    assert len(calls) == 6
    assert result_config["children"][0]["media_error"] == "failed"
    assert "6" in result_config["children"][7]["media_error"]


@pytest.mark.parametrize(
    "node",
    [
        {"type": "card", "color": "#f00", "children": [{"type": "text", "text": "x"}]},
        {"type": "image", "url": "file:///etc/passwd", "alt": "x"},
        {"type": "image", "url": "https://example.com/x", "alt": "x", "media_data": "data:image/png;base64,abc"},
        {"type": "iframe", "url": "https://example.com", "title": "x", "html": "<script/>"},
        {"type": "iframe", "url": "https://example.com", "title": "x", "height": 1201},
        {"type": "map", "latitude": 90, "longitude": 180},
        {"type": "map", "latitude": 0, "longitude": 181},
    ],
)
def test_media_contract_rejects_unsafe_or_out_of_range_fields(node):
    with pytest.raises(ValueError):
        UIBlock.model_validate({"children": [node]})
