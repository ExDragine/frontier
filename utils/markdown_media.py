"""Preload public media into an offline, screenshot-native message document."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import ipaddress
import json
import math
import socket
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx2
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageOps

from utils.http_client import AsyncClient

MAX_MEDIA = 6
MAX_BYTES = 20_000_000
USER_AGENT = "Frontier-message-media/1.0 (+https://github.com/ExDragine/frontier)"
FAKE_IP_NETWORK = ipaddress.ip_network("198.18.0.0/15")


class FakeIPAddress(ValueError):
    def __init__(self, host: str):
        self.host = host
        super().__init__("Fake-IP DNS answer")


def check_public_ips(ips):
    if not ips or any(not ip.is_global or ip.is_multicast or getattr(ip, "ipv4_mapped", None) for ip in ips):
        raise ValueError("Non-public network address")


async def public_address(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTP(S) URLs are supported")
    if parsed.port not in {None, 80, 443}:
        raise ValueError("Unsupported port")
    addresses = await asyncio.get_running_loop().getaddrinfo(
        parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM
    )
    ips = [ipaddress.ip_address(entry[4][0]) for entry in addresses]
    try:
        ipaddress.ip_address(parsed.hostname)
        literal = True
    except ValueError:
        literal = False
    if not literal and ips and all(ip.version == 4 and ip in FAKE_IP_NETWORK for ip in ips):
        raise FakeIPAddress(parsed.hostname)
    check_public_ips(ips)
    return str(ips[0]), parsed.hostname


class PublicRedirect(Exception):
    def __init__(self, url: str):
        self.url = url


class PublicFetcher:
    """Pin every connection to validated DNS, including redirects and browser subresources."""

    def __init__(self, client: AsyncClient, cache_dir: Path, *, fake_ip_fallback: bool = False):
        self.client = client
        self.cache_dir = cache_dir
        self.bytes = 0
        self.requests = 0
        self.fake_ip_fallback = fake_ip_fallback
        self.dns_cache = {}
        self.dns_lock = asyncio.Lock()

    async def address(self, url: str) -> tuple[str, str]:
        try:
            return await public_address(url)
        except FakeIPAddress as exc:
            if not self.fake_ip_fallback:
                raise
            host = exc.host
        async with self.dns_lock:
            if host not in self.dns_cache:
                self.dns_cache[host] = await self.public_dns(host)
            return self.dns_cache[host], host

    async def public_dns(self, host: str) -> str:
        # Bootstrap by a fixed public IP: the resolver's hostname may itself
        # resolve to Fake-IP. Preserve TLS hostname verification and Host.
        target = httpx2.URL("https://cloudflare-dns.com/dns-query").copy_with(host="1.1.1.1")
        headers = {
            "Host": "cloudflare-dns.com",
            "Accept": "application/dns-json",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        }
        async with self.client.stream(
            "GET",
            target,
            params={"name": host, "type": "A"},
            headers=headers,
            extensions={"sni_hostname": "cloudflare-dns.com"},
            follow_redirects=False,
        ) as response:
            response.raise_for_status()
            if response.is_redirect or response.headers.get("content-encoding", "identity") != "identity":
                raise ValueError("Unexpected public DNS response")
            data = bytearray()
            async for chunk in response.aiter_raw(chunk_size=8192):
                data.extend(chunk)
                self.bytes += len(chunk)
                if len(data) > 65536 or self.bytes > MAX_BYTES:
                    raise ValueError("Public DNS response size limit")
            answer = json.loads(data)
            if answer.get("Status") != 0 or answer.get("TC"):
                raise ValueError("Public DNS query failed")
            ips = [ipaddress.ip_address(record["data"]) for record in answer.get("Answer", []) if record["type"] == 1]
            check_public_ips(ips)
            return str(ips[0])

    async def get(self, url: str, *, limit: int = 3_000_000, redirects: int = 0, follow_redirects: bool = True):
        if redirects > 4 or self.requests >= 100:
            raise ValueError("Resource request limit")
        self.requests += 1
        cached = self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".png")
        tile = urlsplit(url).hostname in {
            "tile.openstreetmap.org",
            "a.tile.openstreetmap.org",
            "b.tile.openstreetmap.org",
            "c.tile.openstreetmap.org",
        }
        if tile and cached.is_file() and time.time() - cached.stat().st_mtime < 7 * 86400:
            body = cached.read_bytes()
            self.bytes += len(body)
            if len(body) > limit or self.bytes > MAX_BYTES:
                raise ValueError("Resource size limit")
            return body, "image/png"
        ip, host = await self.address(url)
        target = httpx2.URL(url)
        pinned = target.copy_with(host=ip)
        headers = {"Host": target.netloc.decode(), "User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        async with self.client.stream(
            "GET", pinned, headers=headers, extensions={"sni_hostname": host}, follow_redirects=False
        ) as response:
            if response.is_redirect:
                location = urljoin(url, response.headers["location"])
                if not follow_redirects:
                    await self.address(location)
                    raise PublicRedirect(location)
                return await self.get(location, limit=limit, redirects=redirects + 1)
            response.raise_for_status()
            if response.headers.get("content-encoding", "identity") != "identity":
                raise ValueError("Compressed resource not supported")
            chunks = []
            size = 0
            async for chunk in response.aiter_raw(chunk_size=65536):
                size += len(chunk)
                self.bytes += len(chunk)
                if size > limit or self.bytes > MAX_BYTES:
                    raise ValueError("Resource size limit")
                chunks.append(chunk)
            body = b"".join(chunks)
            mime = response.headers.get("content-type", "application/octet-stream")
            if tile and mime.startswith("image/png"):
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(body)
            return body, mime

    async def route(self, route):
        request = route.request
        if request.method != "GET" or request.resource_type in {"media", "websocket", "eventsource"}:
            await route.abort()
            return
        try:
            body, mime = await self.get(request.url, follow_redirects=False)
            await route.fulfill(status=200, content_type=mime, body=body)
        except PublicRedirect as redirect:
            await route.fulfill(status=302, headers={"location": redirect.url}, body="")
        except Exception:
            await route.abort()


def raster_data(body: bytes) -> tuple[str, int, int]:
    with Image.open(io.BytesIO(body)) as source:
        if source.width * source.height > 20_000_000:
            raise ValueError("Image pixel limit")
        image = ImageOps.exif_transpose(source).convert("RGBA")
        image.thumbnail((2000, 2000))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode(), image.width, image.height


async def render_map(node: dict, fetcher: PublicFetcher, width: int) -> bytes:
    """Compose only the currently visible OSM tiles in Web Mercator coordinates."""
    zoom, height = node["zoom"], node["height"]
    scale = 256 * 2**zoom
    center_x = (node["longitude"] + 180) / 360 * scale
    center_y = (1 - math.asinh(math.tan(math.radians(node["latitude"]))) / math.pi) / 2 * scale
    left, top = math.floor(center_x - width / 2), math.floor(center_y - height / 2)
    picture = Image.new("RGBA", (width, height), "#f4f4f5")

    async def tile(x, y):
        url = f"https://tile.openstreetmap.org/{zoom}/{x % 2**zoom}/{y}.png"
        body, _ = await fetcher.get(url)
        with Image.open(io.BytesIO(body)) as source:
            if source.size != (256, 256):
                raise ValueError("Unexpected map tile")
            picture.paste(source.convert("RGBA"), (x * 256 - left, y * 256 - top))

    async with asyncio.TaskGroup() as group:
        for x in range(left // 256, (left + width - 1) // 256 + 1):
            for y in range(top // 256, (top + height - 1) // 256 + 1):
                if 0 <= y < 2**zoom:
                    group.create_task(tile(x, y))
    draw = ImageDraw.Draw(picture)
    x, y = center_x - left, center_y - top
    draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill="#1d4ed8", outline="white", width=3)
    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="white")
    output = io.BytesIO()
    picture.save(output, format="PNG")
    return output.getvalue()


async def capture_frame(
    browser, fetcher: PublicFetcher, url: str, width: int, height: int, *, full_page=False
) -> bytes:
    await fetcher.address(url)
    context = await browser.new_context(
        viewport={"width": width, "height": height}, service_workers="block", accept_downloads=False
    )
    try:
        await context.route("**/*", fetcher.route)
        await context.route_web_socket("**/*", lambda ws: ws.close())
        page = await context.new_page()
        page.on("popup", lambda popup: popup.close())
        await page.goto(url, wait_until="domcontentloaded", timeout=12_000)
        await page.wait_for_function(
            "document.body && (document.body.innerText.trim().length > 0 || document.querySelector('canvas,svg,img')) && "
            "[...document.images].every(i => i.complete)",
            timeout=8000,
        )
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(600)
        if full_page:
            content_height = await page.evaluate(
                "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
            )
            await page.set_viewport_size({"width": width, "height": min(max(height, int(content_height)), 1200)})
        return await page.screenshot(type="png", animations="disabled")
    finally:
        await context.close()


async def load_media(node: dict, browser, fetcher: PublicFetcher, width: int) -> None:
    try:
        async with asyncio.timeout(20):
            if node["type"] == "image":
                body, _ = await fetcher.get(node["url"], limit=10_000_000)
            elif node["type"] == "map":
                lat, lon, zoom = node["latitude"], node["longitude"], node["zoom"]
                node["source_url"] = (
                    f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map={zoom}/{lat:.6f}/{lon:.6f}"
                )
                body = await render_map(node, fetcher, width)
            else:
                node["source_url"] = node["url"]
                body = await capture_frame(
                    browser, fetcher, node["url"], width, node["height"], full_page=node.get("full_page", False)
                )
            node["media_data"], node["media_width"], node["media_height"] = raster_data(body)
            if node.get("full_page") and node["media_height"] >= 1200:
                node["capture_note"] = "网页较长，此处展示前 1200 像素，请通过原链接查看完整页面。"
            node.pop("media_error", None)
    except Exception:
        # Do not disclose network errors or internal addresses in QQ content/logs.
        node["media_error"] = "素材未能加载，请查看原链接。"


def media_nodes(node: dict):
    if node.get("type") in {"image", "iframe", "map"}:
        yield node
    for child in node.get("children", []):
        yield from media_nodes(child)


async def prepare_media(html_content: str, browser, *, width: int, cache_dir: Path) -> str:
    from utils.configs import EnvConfig

    soup = BeautifulSoup(html_content, "html.parser")
    documents = []
    nodes = []
    for placeholder in soup.select('[data-rich-kind="ui"]'):
        config = json.loads(placeholder["data-rich-config"])
        documents.append((placeholder, config))
        nodes.extend(media_nodes(config))
    if not nodes:
        return html_content
    async with AsyncClient(
        trust_env=False, timeout=8, limits=httpx2.Limits(max_keepalive_connections=0, max_connections=12)
    ) as client:
        fetcher = PublicFetcher(client, cache_dir, fake_ip_fallback=EnvConfig.MESSAGE_MEDIA_FAKE_IP_FALLBACK)
        slots = asyncio.Semaphore(3)

        async def load(node):
            async with slots:
                await load_media(node, browser, fetcher, min(max(width - (36 if width <= 600 else 96), 200), 1200))

        for index, node in enumerate(nodes):
            node["media_error"] = (
                "素材加载超时，请查看原链接。" if index < MAX_MEDIA else "本条回复最多加载 6 个媒体模块。"
            )
        try:
            async with asyncio.timeout(25):
                await asyncio.gather(*(load(node) for node in nodes[:MAX_MEDIA]))
        except TimeoutError:
            pass
    for placeholder, config in documents:
        placeholder["data-rich-config"] = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    return str(soup)
