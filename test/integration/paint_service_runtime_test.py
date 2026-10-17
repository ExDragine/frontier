# ruff: noqa: S101
"""Real OpenAI SDK serialization and provider-protocol routing without network access."""

import subprocess
import sys
from pathlib import Path


def test_real_paint_sdk_routes_serializes_and_downloads_images(tmp_path):
    script = r'''
import asyncio
import base64
import io
import json
import socket
import sys
from email import policy
from email.parser import BytesParser

sys.path.insert(0, sys.argv[1])
from httpx2 import AsyncClient, ByteStream, MockTransport, Response
from openai import AsyncOpenAI
from PIL import Image
from utils import paint_service as service
from utils.configs import EnvConfig

buffer = io.BytesIO()
Image.new("RGB", (4, 4), "blue").save(buffer, format="PNG")
png = buffer.getvalue()
encoded = base64.b64encode(png).decode()

async def main():
    async def dns(host, port, **kwargs):
        ip = "127.0.0.1" if host == "127.0.0.1" else "8.8.8.8"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]
    asyncio.get_running_loop().getaddrinfo = dns

    for case in ("generate", "edit", "url", "bad_url_body", "private_url", "404", "responses", "responses_edit"):
        calls, clients, downloads = [], [], []
        mode = "responses" if case.startswith("responses") else "chat_completions"
        EnvConfig.reload({"config_version": 2, "models": {
            "paint_model": "contract-image", "paint_model_provider": "media",
            "paint_size": "1536x1024", "paint_quality": "high",
        }, "providers": {"media": {
            "type": "openai", "api_mode": mode, "api_key": "contract-key", "base_url": "https://api.example/v1",
        }}})

        def handler(request):
            calls.append(request)
            assert request.headers["authorization"] == "Bearer contract-key"
            if case == "404":
                return Response(404, json={"error": {"message": "unsupported", "type": "not_found"}})
            if case == "edit":
                assert request.url.path == "/v1/images/edits"
                content_type = request.headers["content-type"]
                assert content_type.startswith("multipart/form-data;")
                mime = BytesParser(policy=policy.default).parsebytes(
                    ("Content-Type: " + content_type + "\r\n\r\n").encode() + request.content
                )
                files, fields = [], {}
                for part in mime.iter_parts():
                    name = part.get_param("name", header="content-disposition")
                    if part.get_filename():
                        assert name == "image[]" and part.get_content_type() == "image/png"
                        files.append(part.get_filename())
                        with Image.open(io.BytesIO(part.get_payload(decode=True))) as image:
                            image.verify()
                    else:
                        fields[name] = part.get_payload(decode=True).decode()
                assert files == ["reference-1.png", "reference-2.png"]
                assert fields["model"] == "contract-image" and fields["prompt"] == "a blue circle"
                assert fields["size"] == "1536x1024" and fields["quality"] == "high"
            else:
                body = json.loads(request.content)
                assert body["model"] == "contract-image"
                if mode == "responses":
                    assert request.url.path == "/v1/responses" and "prompt" not in body
                    assert body["tool_choice"] == {"type": "image_generation"}
                    assert body["tools"][0]["action"] == ("edit" if case == "responses_edit" else "generate")
                    return Response(200, json={"id": "resp-test", "output": [{
                        "type": "image_generation_call", "id": "ig-test", "result": encoded,
                    }]})
                assert request.url.path == "/v1/images/generations" and "input" not in body
                assert body["prompt"] == "a blue circle" and body["n"] == 1
                assert body["output_format"] == "png" and "response_format" not in body
            if case in {"url", "bad_url_body", "private_url"}:
                url = "http://127.0.0.1/private" if case == "private_url" else "https://cdn.example/image.png?sig=signed"
                return Response(200, json={"created": 1, "data": [{"url": url}]})
            return Response(200, json={"created": 1, "data": [{"b64_json": encoded}]})

        def download(request):
            downloads.append(request)
            assert request.url.host == "8.8.8.8" and request.headers["host"] == "cdn.example"
            assert request.extensions["sni_hostname"] == "cdn.example"
            assert "authorization" not in request.headers and "cookie" not in request.headers
            return Response(200, headers={"content-type": "image/png"},
                            stream=ByteStream(b"<html>not an image</html>" if case == "bad_url_body" else png))

        def build(**kwargs):
            client = AsyncOpenAI(**kwargs, max_retries=0, http_client=AsyncClient(transport=MockTransport(handler)))
            clients.append(client)
            return client

        service.AsyncOpenAI = build
        async with AsyncClient(transport=MockTransport(download)) as downloader:
            service.get_http_client = lambda name: downloader
            result = await service.paint("a blue circle", [png, png] if case in {"edit", "responses_edit"} else [])
        assert len(calls) == 1, (case, len(calls))
        assert all(client.is_closed() for client in clients)
        if case in {"404", "private_url", "bad_url_body"}:
            assert result is None, case
        else:
            assert result == png, case
        assert len(downloads) == (1 if case in {"url", "bad_url_body"} else 0), case

asyncio.run(main())
'''
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[2])],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
