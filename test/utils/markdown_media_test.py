# ruff: noqa: S101
import gzip
import io
import json
import socket
import zlib
from types import SimpleNamespace

import httpx2
import pytest
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from playwright.async_api import TimeoutError as BrowserTimeoutError

from utils import markdown_media as media
from utils.markdown_rich import UIBlock


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (640, 320), "#60a5fa").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
@pytest.mark.parametrize("encoding,compress", [("gzip", gzip.compress), ("deflate", zlib.compress)])
async def test_compressed_body_is_decoded_with_expansion_limit(tmp_path, encoding, compress):
    body = b"<html><body>page content</body></html>"
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda r: httpx2.Response(
                200, headers={"content-encoding": encoding}, stream=httpx2.ByteStream(compress(body))
            )
        )
    ) as client:
        fetcher = media.PublicFetcher(client, tmp_path)
        async with client.stream("GET", "https://public.example") as response:
            assert await fetcher.read_body(response, 1000) == body
        async with client.stream("GET", "https://public.example") as response:
            with pytest.raises(media.MediaFailure, match="大小限制"):
                await fetcher.read_body(response, 5)


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [gzip.compress(b"x" * 1_000_000), gzip.compress(b"html")[:-4], b"invalid"])
async def test_compression_bombs_and_damaged_streams_are_rejected(tmp_path, body):
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda r: httpx2.Response(200, headers={"content-encoding": "gzip"}, stream=httpx2.ByteStream(body))
        )
    ) as client:
        async with client.stream("GET", "https://public.example") as response:
            with pytest.raises(media.MediaFailure):
                await media.PublicFetcher(client, tmp_path).read_body(response, 1024)


@pytest.mark.asyncio
async def test_frame_slow_images_do_not_discard_loaded_document(tmp_path):  # noqa: C901 - browser test doubles
    waits = []

    class Page:
        def on(self, *args):
            pass

        async def goto(self, *args, **kwargs):
            pass

        async def wait_for_function(self, script, **kwargs):
            waits.append(script)
            if "document.images" in script:
                raise BrowserTimeoutError("slow private URL should not leak")

        async def evaluate(self, script):
            return None

        async def wait_for_timeout(self, *args):
            pass

        async def screenshot(self, **kwargs):
            return png()

    class Context:
        closed = False

        async def route(self, *args):
            pass

        async def route_web_socket(self, *args):
            pass

        async def new_page(self):
            return Page()

        async def close(self):
            self.closed = True

    context = Context()

    class Browser:
        async def new_context(self, **kwargs):
            return context

    class Fetcher:
        async def address(self, url):
            return "8.8.8.8", "public.example"

    assert await media.capture_frame(Browser(), Fetcher(), "https://public.example", 500, 420) == png()
    assert "document.images" not in waits[0] and context.closed


def test_failure_reason_reports_status_without_private_urls():
    error = httpx2.HTTPStatusError(
        "secret http://127.0.0.1/private",
        request=httpx2.Request("GET", "https://example.com"),
        response=httpx2.Response(403),
    )
    assert media.failure_reason(error) == "来源返回 HTTP 403"
    assert media.failure_reason(ExceptionGroup("secret", [error])) == "来源返回 HTTP 403"


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
async def test_fake_ip_fallback_uses_real_public_ip_and_coalesces_dns(monkeypatch, tmp_path):
    async def dns(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("198.18.0.7", 443))]

    monkeypatch.setattr(media.asyncio.get_running_loop(), "getaddrinfo", dns)
    seen = []

    def handler(request):
        seen.append(request)
        if request.url.host == "1.1.1.1":
            payload = {"Status": 0, "Answer": [{"type": 5, "data": "cdn.example"}, {"type": 1, "data": "8.8.8.8"}]}
            return httpx2.Response(200, stream=httpx2.ByteStream(json.dumps(payload).encode()))
        return httpx2.Response(200, stream=httpx2.ByteStream(b"loaded"))

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        fetcher = media.PublicFetcher(client, tmp_path, fake_ip_fallback=True)
        results = await media.asyncio.gather(*(fetcher.get(f"https://public.example/{i}") for i in range(3)))
    assert all(body == b"loaded" for body, _ in results)
    assert len(seen) == 4
    assert seen[0].url.host == "1.1.1.1" and seen[0].url.params["name"] == "public.example"
    assert seen[0].headers["host"] == seen[0].extensions["sni_hostname"] == "cloudflare-dns.com"
    assert all(r.url.host == "8.8.8.8" and r.headers["host"] == "public.example" for r in seen[1:])
    assert all(r.extensions["sni_hostname"] == "public.example" for r in seen[1:])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answers", [[], ["127.0.0.1"], ["10.0.0.1"], ["169.254.169.254"], ["198.18.0.8"], ["8.8.8.8", "192.168.1.1"]]
)
async def test_fake_ip_resolver_cannot_authorize_private_targets(monkeypatch, tmp_path, answers):
    async def address(url):
        raise media.FakeIPAddress("public.example")

    monkeypatch.setattr(media, "public_address", address)
    seen = []

    def handler(request):
        seen.append(request)
        return httpx2.Response(
            200,
            stream=httpx2.ByteStream(
                json.dumps({"Status": 0, "Answer": [{"type": 1, "data": ip} for ip in answers]}).encode()
            ),
        )

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        with pytest.raises(ValueError):
            await media.PublicFetcher(client, tmp_path, fake_ip_fallback=True).get("https://public.example/x")
    assert len(seen) == 1 and seen[0].url.host == "1.1.1.1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,ips,enabled",
    [
        ("https://public.example/x", ["198.18.0.1"], False),
        ("https://198.18.0.1/x", ["198.18.0.1"], True),
        ("https://public.example/x", ["198.18.0.1", "127.0.0.1"], True),
        ("https://private.example/x", ["192.168.1.1"], True),
    ],
)
async def test_fake_ip_mode_preserves_local_address_restrictions(monkeypatch, tmp_path, url, ips, enabled):
    async def dns(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in ips]

    monkeypatch.setattr(media.asyncio.get_running_loop(), "getaddrinfo", dns)
    seen = []
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(lambda r: seen.append(r))) as client:
        with pytest.raises(ValueError):
            await media.PublicFetcher(client, tmp_path, fake_ip_fallback=enabled).get(url)
    assert seen == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {"Status": 3},
        {"Status": 0, "TC": True},
        {"Status": 0, "Answer": [{"type": 1, "data": "not-an-ip"}]},
    ],
)
async def test_fake_ip_resolver_rejects_invalid_answers(tmp_path, response):
    async with httpx2.AsyncClient(
        transport=httpx2.MockTransport(
            lambda r: httpx2.Response(200, stream=httpx2.ByteStream(json.dumps(response).encode()))
        )
    ) as client:
        with pytest.raises(ValueError):
            await media.PublicFetcher(client, tmp_path).public_dns("public.example")


@pytest.mark.asyncio
async def test_fake_ip_resolver_does_not_follow_redirects(tmp_path):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx2.Response(302, headers={"location": "http://127.0.0.1/"})

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        with pytest.raises((ValueError, httpx2.HTTPStatusError)):
            await media.PublicFetcher(client, tmp_path).public_dns("public.example")
    assert len(seen) == 1


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


@pytest.mark.asyncio
async def test_map_wraps_dateline_tiles_and_marks_exact_center():
    requested = []
    buffer = io.BytesIO()
    Image.new("RGB", (256, 256), "#dbeafe").save(buffer, format="PNG")

    class Fetcher:
        async def get(self, url):
            requested.append(url)
            return buffer.getvalue(), "image/png"

    body = await media.render_map({"latitude": 0, "longitude": 180, "zoom": 2, "height": 420}, Fetcher(), 900)
    assert len(requested) == 8
    assert all(url.startswith("https://tile.openstreetmap.org/2/") for url in requested)
    assert {int(url.split("/")[-2]) for url in requested} == {0, 1, 2, 3}
    image = Image.open(io.BytesIO(body))
    assert image.size == (900, 420)
    assert image.getpixel((450, 210))[:3] == (255, 255, 255)
    assert image.getpixel((450, 203))[:3] == (29, 78, 216)
