import secrets
import time
from collections import defaultdict
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.configs import EnvConfig

security = HTTPBearer()

# 登录限流：记录每个 IP 的登录尝试
_login_attempts = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 分钟


def create_token(subject: str = "admin") -> str:
    """生成 JWT token"""
    payload = {
        "sub": subject,
        "iat": int(time.time()),
        "exp": int(time.time()) + EnvConfig.DASHBOARD_JWT_EXPIRE_HOURS * 3600,
    }
    return jwt.encode(payload, EnvConfig.DASHBOARD_JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict:
    """验证并解码 JWT token，失败时抛出异常"""
    try:
        payload = jwt.decode(token, EnvConfig.DASHBOARD_JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


def verify_password(password: str) -> bool:
    """验证密码"""
    return secrets.compare_digest(password, EnvConfig.DASHBOARD_PASSWORD)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI 依赖：要求请求携带有效的 JWT token"""
    return verify_token(credentials.credentials)


def check_rate_limit(ip: str) -> bool:
    """检查登录频率限制，返回 True 表示允许，False 表示超过限制"""
    now = time.time()
    # 清理过期的记录
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < WINDOW_SECONDS]

    if len(_login_attempts[ip]) >= MAX_ATTEMPTS:
        return False

    _login_attempts[ip].append(now)
    return True
