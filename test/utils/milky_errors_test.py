# ruff: noqa: S101, S105, S106

import json

import pytest
from nonebot.adapters.milky.exception import ActionFailed

from utils.milky_errors import milky_error_details


def test_milky_diagnostics_only_extract_known_fields():
    exc = ActionFailed(status="failed", retcode=1200, message="消息过长，发送失败 {50%}",
                       data={"token": "hidden-data", "text": "private-message"}, secret="hidden-secret")
    assert milky_error_details(exc) == (
        ' milky_status=failed milky_retcode=1200 milky_message="消息过长，发送失败 {50%}"'
    )


@pytest.mark.parametrize("message, secrets", [
    ('发送失败 api_key=top-secret password="secret with spaces"', ["top-secret", "secret with spaces"]),
    ('发送失败 {"access_token":"access-secret", "refresh_token":"refresh-secret"}', ["access-secret", "refresh-secret"]),
    ("发送失败 Authorization: Bearer auth-secret\nCookie: session=cookie-secret", ["auth-secret", "cookie-secret"]),
    ('发送失败 {"Cookie":"sid=cookie-secret"}', ["cookie-secret"]),
    ("发送失败 Bearer bearer-secret sk-key-secret", ["bearer-secret", "sk-key-secret"]),
    ("发送失败 https://user:pass@private.example/x?token=signed-secret", ["user:pass", "private.example", "signed-secret"]),
    (r"发送失败 C:\Users\PrivateUser\message.txt /home/private/message.txt", ["PrivateUser", "/home/private"]),
    ("发送失败 qq=123456789 group=987654321 phone=13800138000 user=private@example.com", ["123456789", "987654321", "13800138000", "private@example.com"]),
    ('发送失败 {"text":"private payload", "segments":["more private data"]}', ["private payload", "more private data"]),
    ('发送失败 data={"unknown":"private-data"}', ["private-data"]),
])
def test_milky_message_redacts_credentials_payload_and_identifiers(message, secrets):
    details = milky_error_details(ActionFailed(status="failed", retcode=1200, message=message))
    assert "发送失败" in details
    assert "milky_retcode=1200" in details
    assert all(secret not in details for secret in secrets)


@pytest.mark.parametrize("escaped", [False, True])
def test_milky_message_removes_echoed_request_text(escaped):
    text = '私聊正文\n第二行 "quoted"'
    echoed = json.dumps(text, ensure_ascii=True)[1:-1] if escaped else text
    exc = ActionFailed(status="failed", retcode=100, message="发送失败 " + echoed)
    details = milky_error_details(exc, sensitive={"nodes": [{"text": text}]})
    assert "[content]" in details
    assert "正文" not in details and "quoted" not in details and "\\u79c1" not in details


def test_milky_message_removes_truncated_request_echo():
    text = "this is a private long user message that the server truncated"
    details = milky_error_details(ActionFailed(status="failed", retcode=1200, message="消息发送失败 " + text[:12] + "…"),
                                  sensitive={"text": text})
    assert "消息发送失败" in details and "this is" not in details


def test_milky_diagnostics_bound_message_and_remove_log_injection():
    details = milky_error_details(ActionFailed(status="failed", retcode="-1200", message="失败\r\n\x00\x1b\u202e" + "长" * 2000))
    message = json.loads(details.split(" milky_message=", 1)[1])
    assert len(message) == 512 and message.endswith("…")
    assert not any(char in details for char in ("\n", "\r", "\x00", "\x1b", "\u202e"))


def test_milky_diagnostics_do_not_stringify_unknown_fields_or_exceptions():
    class Secret:
        def __str__(self):
            pytest.fail("diagnostics stringified an untrusted object")

    details = milky_error_details(ActionFailed(status=Secret(), retcode=Secret(), message=Secret(), data=Secret()))
    assert details == ' milky_status=unknown milky_retcode=unknown milky_message=""'
    assert milky_error_details(RuntimeError("private-exception")) == ""


def test_milky_diagnostics_unwrap_chained_errors_and_stop_at_cycles():
    root = ActionFailed(status="failed", retcode=1200, message="发送失败")
    wrapper = RuntimeError("private wrapper")
    wrapper.__cause__ = root
    assert "milky_retcode=1200" in milky_error_details(wrapper)
    assert "private wrapper" not in milky_error_details(wrapper)
    wrapper.__cause__ = wrapper
    assert milky_error_details(wrapper) == ""
