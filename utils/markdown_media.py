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
from urllib.parse import urlencode, urljoin, urlsplit

import httpx2
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

from utils.http_client import AsyncClient

MAX_MEDIA = 6
MAX_BYTES = 20_000_000
USER_AGENT = "Frontier-message-media/1.0 (+https://github.com/ExDragine/frontier)"


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
    if not ips or any(not ip.is_global or ip.is_multicast or getattr(ip, "ipv4_mapped", None) for ip in ips):
        raise ValueError("Non-public network address")
    return str(ips[0]), parsed.hostname


class PublicRedirect(Exception):
    def __init__(self, url: str):
        self.url = url


class PublicFetcher:
    """Pin every connection to validated DNS, including redirects and browser subresources."""

    def __init__(self, client: AsyncClient, cache_dir: Path):
        self.client = client
        self.cache_dir = cache_dir
        self.bytes = 0
        self.requests = 0

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
        ip, host = await public_address(url)
        target = httpx2.URL(url)
        pinned = target.copy_with(host=ip)
        headers = {"Host": target.netloc.decode(), "User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        async with self.client.stream(
            "GET", pinned, headers=headers, extensions={"sni_hostname": host}, follow_redirects=False
        ) as response:
            if response.is_redirect:
                location = urljoin(url, response.headers["location"])
                if not follow_redirects:
                    await public_address(location)
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


def map_url(node: dict, width: int) -> str:
    lat, lon, zoom = node["latitude"], node["longitude"], node["zoom"]
    scale = 256 * 2**zoom
    x = (lon + 180) / 360 * scale
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * scale

    def latitude(pixel):
        return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * pixel / scale))))

    west, east = ((x + delta) / scale * 360 - 180 for delta in (-width / 2, width / 2))
    south, north = (latitude(y + delta) for delta in (node["height"] / 2, -node["height"] / 2))
    params = {"bbox": f"{west},{south},{east},{north}", "layer": "mapnik", "marker": f"{lat},{lon}"}
    return "https://www.openstreetmap.org/export/embed.html?" + urlencode(params)


async def capture_frame(browser, fetcher: PublicFetcher, url: str, width: int, height: int, *, is_map=False) -> bytes:
    await public_address(url)
    context = await browser.new_context(
        viewport={"width": width, "height": height}, service_workers="block", accept_downloads=False
    )
    try:
        await context.route("**/*", fetcher.route)
        await context.route_web_socket("**/*", lambda ws: ws.close())
        page = await context.new_page()
        page.on("popup", lambda popup: popup.close())
        await page.goto(url, wait_until="domcontentloaded", timeout=12_000)
        if is_map:
            await page.wait_for_function(
                "document.querySelectorAll('.leaflet-tile').length > 0 && "
                "[...document.querySelectorAll('.leaflet-tile')].every(i => i.complete && i.naturalWidth > 0)",
                timeout=8000,
            )
        else:
            await page.wait_for_function(
                "document.body && (document.body.innerText.trim().length > 0 || document.querySelector('canvas,svg,img')) && "
                "[...document.images].every(i => i.complete)",
                timeout=8000,
            )
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(600)
        return await page.screenshot(type="png", animations="disabled")
    finally:
        await context.close()


async def load_media(node: dict, browser, fetcher: PublicFetcher, width: int) -> None:
    try:
        async with asyncio.timeout(20):
            if node["type"] == "image":
                body, _ = await fetcher.get(node["url"], limit=10_000_000)
            else:
                url = map_url(node, width) if node["type"] == "map" else node["url"]
                node["source_url"] = url
                body = await capture_frame(browser, fetcher, url, width, node["height"], is_map=node["type"] == "map")
            node["media_data"], node["media_width"], node["media_height"] = raster_data(body)
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
        fetcher = PublicFetcher(client, cache_dir)
        slots = asyncio.Semaphore(3)

        async def load(node):
            async with slots:
                await load_media(node, browser, fetcher, min(max(width - 96, 320), 1200))

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
