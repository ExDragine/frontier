# ruff: noqa: S101

import logging
import time

import bcrypt
import jwt
import pytest
from fastapi import HTTPException

from plugins.dashboard import auth


def test_create_and_verify_token(monkeypatch):
    token = auth.create_token("admin")
    payload = auth.verify_token(token)
    assert payload["sub"] == "admin"


def test_verify_token_expired(monkeypatch):
    payload = {"sub": "admin", "iat": int(time.time()) - 10, "exp": int(time.time()) - 1}
    token = jwt.encode(payload, auth.EnvConfig.DASHBOARD_JWT_SECRET, algorithm="HS256")
    with pytest.raises(HTTPException):
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


def test_verify_password_accepts_bcrypt_hash(monkeypatch):
    configured = "hashed-dashboard-secret"
    hashed = bcrypt.hashpw(configured.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8")
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", hashed)

    assert auth.verify_password(configured) is True
    assert auth.verify_password("wrong") is False


def test_verify_password_plaintext_config_derives_hash(monkeypatch):
    configured = "legacy-plaintext-secret"
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", configured)

    assert auth.verify_password(configured) is True
    assert auth.verify_password("legacy-plaintext-secre") is False
    assert auth.verify_password("") is False


def test_derived_hash_cache_follows_config_change(monkeypatch):
    """缓存键是配置值本身：reload 换掉明文后不能继续认旧口令。"""
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", "first-configured-secret")
    assert auth.verify_password("first-configured-secret") is True

    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", "second-configured-secret")

    assert auth.verify_password("second-configured-secret") is True
    assert auth.verify_password("first-configured-secret") is False


def test_plaintext_warning_logged_once_without_secret(monkeypatch, caplog):
    configured = "rotate-me-warning-secret"
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", configured)
    auth._warn_legacy_password.cache_clear()

    with caplog.at_level(logging.WARNING, logger=auth.__name__):
        assert auth.verify_password(configured) is True
        assert auth.verify_password(configured) is True

    warnings = [record for record in caplog.records if "明文" in record.getMessage()]
    assert len(warnings) == 1
    assert all(configured not in record.getMessage() for record in caplog.records)


def test_bcrypt_config_does_not_warn(monkeypatch, caplog):
    configured = "hashed-without-warning"
    hashed = bcrypt.hashpw(configured.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8")
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", hashed)

    with caplog.at_level(logging.WARNING, logger=auth.__name__):
        assert auth.verify_password(configured) is True

    assert not [record for record in caplog.records if "明文" in record.getMessage()]


def test_plaintext_longer_than_bcrypt_limit_is_truncated(monkeypatch, caplog):
    """明文超过 72 字节时按 bcrypt 语义截断，旧部署仍可登录。"""
    configured = "x" * 100
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", configured)

    with caplog.at_level(logging.WARNING, logger=auth.__name__):
        assert auth.verify_password(configured) is True
        assert auth.verify_password("x" * 72 + "y" * 28) is True
        assert auth.verify_password("x" * 71) is False

    assert any("72" in record.getMessage() for record in caplog.records)
    assert all(configured not in record.getMessage() for record in caplog.records)


def test_bcrypt_hash_rejects_overlong_candidate_without_error(monkeypatch):
    """bcrypt 库会拒绝超长输入，截断后必须返回 False 而不是抛异常。"""
    configured = "short-secret"
    hashed = bcrypt.hashpw(configured.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8")
    monkeypatch.setattr(auth.EnvConfig, "DASHBOARD_PASSWORD", hashed)

    assert auth.verify_password("y" * 200) is False
