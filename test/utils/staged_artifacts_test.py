# ruff: noqa: S101

import pytest


class DummyUniMessage:
    def __init__(self, content=None):
        self.content = content

    @classmethod
    def image(cls, url=None, path=None, raw=None, **_kwargs):
        return cls({"type": "image", "url": url, "path": str(path) if path else None, "raw": raw})

    @classmethod
    def text(cls, text: str):
        return cls({"type": "text", "text": text})

    def extend(self, other: "DummyUniMessage") -> "DummyUniMessage":
        current = self.content if isinstance(self.content, list) else [self.content]
        incoming = other.content if isinstance(other.content, list) else [other.content]
        self.content = current + incoming
        return self


def test_stage_artifact_response_persists_binary_artifact(monkeypatch, tmp_path):
    from utils import staged_artifacts

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)

    text, original = staged_artifacts.stage_artifact_response("生成完成", DummyUniMessage.image(raw=b"img"))

    assert original.content["raw"] == b"img"
    assert "send_staged_artifact" in text

    artifact_id = text.split('artifact_id="', 1)[1].split('"', 1)[0]
    restored = staged_artifacts.load_staged_artifact(artifact_id, uni_message_cls=DummyUniMessage)

    assert restored.content == {"type": "image", "url": None, "path": None, "raw": b"img"}
    assert (tmp_path / artifact_id / "manifest.json").is_file()
    assert (tmp_path / artifact_id / "blob-1.bin").read_bytes() == b"img"


def test_stage_artifact_rejects_oversized_binary_and_cleans_partial_dir(monkeypatch, tmp_path):
    from utils import staged_artifacts

    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", artifacts_dir)

    with pytest.raises(ValueError, match="暂存内容过大"):
        staged_artifacts.stage_artifact(DummyUniMessage.image(raw=b"too-large"), max_bytes=3)

    assert not artifacts_dir.exists()


def test_cleanup_expired_staged_artifacts_removes_only_old_entries(monkeypatch, tmp_path):
    from utils import staged_artifacts

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(staged_artifacts.time, "time", lambda: 1000.0)

    old_id = staged_artifacts.stage_artifact(DummyUniMessage.image(raw=b"old"), created_at=800.0)
    fresh_id = staged_artifacts.stage_artifact(DummyUniMessage.image(raw=b"fresh"), created_at=990.0)

    cleaned = staged_artifacts.cleanup_expired_staged_artifacts(ttl_seconds=100)

    assert cleaned == 1
    assert not (tmp_path / old_id).exists()
    assert (tmp_path / fresh_id / "manifest.json").is_file()


def test_extract_and_strip_staged_artifact_handoff_text():
    from utils import staged_artifacts

    text = (
        'ok\n<staged_artifact artifact_id="00000000-0000-4000-8000-000000000000" '
        'send_tool="send_staged_artifact" />\n'
        '主 Agent：请调用 send_staged_artifact(artifact_id="00000000-0000-4000-8000-000000000000") '
        "发送这份内容，不要把 staged_artifact 标签原样发给用户。"
    )

    assert staged_artifacts.extract_staged_artifact_ids(text) == ["00000000-0000-4000-8000-000000000000"]
    assert staged_artifacts.strip_staged_artifact_handoffs(text) == "ok"


def test_load_staged_artifact_rejects_invalid_id(monkeypatch, tmp_path):
    from utils import staged_artifacts

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)

    with pytest.raises(ValueError):
        staged_artifacts.load_staged_artifact("../bad", uni_message_cls=DummyUniMessage)


def test_load_staged_artifact_missing_id_raises_file_not_found(monkeypatch, tmp_path):
    from utils import staged_artifacts

    monkeypatch.setattr(staged_artifacts, "STAGED_ARTIFACTS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        staged_artifacts.load_staged_artifact("00000000-0000-4000-8000-000000000000", uni_message_cls=DummyUniMessage)
