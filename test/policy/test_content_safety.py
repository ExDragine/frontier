# ruff: noqa: S101

from unittest.mock import patch

import pytest

from policy.decisions import Verdict
from policy.policies.content_safety import ContentSafetyPolicy
from policy.snapshots import InputSnapshot, OutputSnapshot

# Minimal valid 1x1 red PNG
_VALID_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'


def _input_snap(**overrides) -> InputSnapshot:
    defaults = {"user_id": "u1", "group_id": 1, "chat_type": "group", "text": "hi"}
    defaults.update(overrides)
    return InputSnapshot(**defaults)


def _output_snap(text: str) -> OutputSnapshot:
    return OutputSnapshot(user_id="u1", group_id=1, text=text)


# ── Fake detectors ──

class FakeTextDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Safe", []


class FakeUnsafeDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Unsafe", ["Violent"]


class FakeControversialDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, text: str):
        return "Controversial", ["Politically Sensitive Topics"]


class FakeFailingTextDetector:
    def __init__(self, model_name: str = ""):
        raise RuntimeError("model unavailable")


class FakeImageDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, img):
        return "normal"


class FakeNsfwImageDetector:
    def __init__(self, model_name: str = ""):
        pass

    async def predict(self, img):
        return "nsfw"


class FakeFailingImageDetector:
    def __init__(self, model_name: str = ""):
        raise RuntimeError("image model unavailable")


# ── Reset module-level detectors between tests ──

@pytest.fixture(autouse=True)
def reset_module_detectors():
    import policy.policies.content_safety as cs

    cs._text_detector = None
    cs._image_detector = None
    yield
    cs._text_detector = None
    cs._image_detector = None


@pytest.mark.asyncio
async def test_input_safe_text_passes():
    with patch("utils.context_check.TextCheck", FakeTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "text_model": "dummy"})
        decision = await policy.evaluate(_input_snap(text="hello"))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_input_unsafe_text_denies():
    with patch("utils.context_check.TextCheck", FakeUnsafeDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "text_model": "dummy"})
        decision = await policy.evaluate(_input_snap(text="bad stuff"))
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "unsafe_text_input"
        assert decision.metadata["reaction"] == 26


@pytest.mark.asyncio
async def test_input_controversial_text_warns():
    with patch("utils.context_check.TextCheck", FakeControversialDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="controversial"))
        assert decision.verdict == Verdict.WARN
        assert decision.metadata["reaction"] == 212


@pytest.mark.asyncio
async def test_input_nsfw_image_denies():
    with (
        patch("utils.context_check.TextCheck", FakeTextDetector),
        patch("utils.context_check.ImageCheck", FakeNsfwImageDetector),
    ):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: _VALID_PNG]))
        assert decision.verdict == Verdict.DENY
        assert decision.reason == "unsafe_image_input"


@pytest.mark.asyncio
async def test_input_safe_image_passes():
    with (
        patch("utils.context_check.TextCheck", FakeTextDetector),
        patch("utils.context_check.ImageCheck", FakeImageDetector),
    ):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input"})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: _VALID_PNG]))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_output_unsafe_text_denies():
    with patch("utils.context_check.TextCheck", FakeUnsafeDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output", "block_message": "blocked!"})
        decision = await policy.evaluate(_output_snap("dangerous"))
        assert decision.verdict == Verdict.DENY
        assert decision.message == "blocked!"


@pytest.mark.asyncio
async def test_output_safe_text_passes():
    with patch("utils.context_check.TextCheck", FakeTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output"})
        decision = await policy.evaluate(_output_snap("innocent"))
        assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_output_empty_text_passes():
    policy = ContentSafetyPolicy()
    policy.configure({"direction": "output"})
    decision = await policy.evaluate(_output_snap(""))
    assert decision.verdict == Verdict.ALLOW


@pytest.mark.asyncio
async def test_input_model_error_allows_when_configured():
    with patch("utils.context_check.TextCheck", FakeFailingTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "on_model_error": "allow"})
        decision = await policy.evaluate(_input_snap(text="hello"))
        assert decision.verdict == Verdict.ALLOW
        assert decision.reason == "content_safety_model_unavailable"
        assert decision.metadata["stage"] == "text_input"


@pytest.mark.asyncio
async def test_input_image_model_error_allows_when_configured():
    with patch("utils.context_check.ImageCheck", FakeFailingImageDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "on_model_error": "allow"})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: _VALID_PNG]))
        assert decision.verdict == Verdict.ALLOW
        assert decision.reason == "content_safety_model_unavailable"
        assert decision.metadata["stage"] == "image_init"


@pytest.mark.asyncio
async def test_output_model_error_raises_by_default():
    with patch("utils.context_check.TextCheck", FakeFailingTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output"})
        with pytest.raises(RuntimeError, match="model unavailable"):
            await policy.evaluate(_output_snap("hello"))


@pytest.mark.asyncio
async def test_input_text_check_disabled_skips_text_detector():
    with patch("utils.context_check.TextCheck", FakeFailingTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "text_enabled": False})
        decision = await policy.evaluate(_input_snap(text="hello"))
        assert decision.verdict == Verdict.ALLOW
        assert decision.reason == "input_safe"


@pytest.mark.asyncio
async def test_input_image_check_disabled_skips_image_detector():
    with patch("utils.context_check.ImageCheck", FakeFailingImageDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "input", "image_enabled": False})
        decision = await policy.evaluate(_input_snap(text="", images=[lambda: _VALID_PNG]))
        assert decision.verdict == Verdict.ALLOW
        assert decision.reason == "input_safe"


@pytest.mark.asyncio
async def test_output_text_check_disabled_skips_text_detector():
    with patch("utils.context_check.TextCheck", FakeFailingTextDetector):
        policy = ContentSafetyPolicy()
        policy.configure({"direction": "output", "text_enabled": False})
        decision = await policy.evaluate(_output_snap("hello"))
        assert decision.verdict == Verdict.ALLOW
        assert decision.reason == "output_text_check_disabled"
