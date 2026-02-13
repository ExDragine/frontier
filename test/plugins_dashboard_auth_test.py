# ruff: noqa: S101

import time

import jwt
import pytest

from plugins.dashboard import auth


def test_create_and_verify_token(monkeypatch):
    token = auth.create_token("admin")
    payload = auth.verify_token(token)
    assert payload["sub"] == "admin"


def test_verify_token_expired(monkeypatch):
    payload = {"sub": "admin", "iat": int(time.time()) - 10, "exp": int(time.time()) - 1}
    token = jwt.encode(payload, auth.EnvConfig.DASHBOARD_JWT_SECRET, algorithm="HS256")
    with pytest.raises(Exception):
        auth.verify_token(token)


def test_check_rate_limit():
    ip = "127.0.0.1"
    auth._login_attempts[ip] = []
    for _ in range(auth.MAX_ATTEMPTS):
        assert auth.check_rate_limit(ip) is True
    assert auth.check_rate_limit(ip) is False


def test_verify_password():
    assert auth.verify_password(auth.EnvConfig.DASHBOARD_PASSWORD) is True
    assert auth.verify_password("wrong") is False
