import functools
import logging
import time
from collections import defaultdict

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.configs import EnvConfig

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
SECURITY_DEPENDENCY = Depends(security)

# 登录限流：记录每个 IP 的登录尝试
_login_attempts = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 分钟

# bcrypt 只接受前 72 字节的输入，超长会直接抛 ValueError；统一按库的限制截断。
_BCRYPT_MAX_BYTES = 72


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
        return jwt.decode(token, EnvConfig.DASHBOARD_JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token 已过期") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="无效的 Token") from exc


def _password_bytes(value: str) -> bytes:
    """按 bcrypt 的 72 字节上限截断候选口令，避免超长输入触发 ValueError。"""
    return value.encode("utf-8")[:_BCRYPT_MAX_BYTES]


@functools.lru_cache(maxsize=8)
def _derive_legacy_hash(stored: str) -> bytes:
    """把明文配置在内存中派生为 bcrypt 哈希。

    缓存键就是配置值本身，所以 ``EnvConfig.reload()`` 换掉明文口令后会重新派生，
    不会把旧口令的派生结果继续用于新配置。
    """
    return bcrypt.hashpw(_password_bytes(stored), bcrypt.gensalt())


@functools.lru_cache(maxsize=8)
def _warn_legacy_password(stored: str) -> None:
    """对每个明文配置值只提示一次；日志不包含口令内容。"""
    logger.warning(
        "Dashboard 口令仍以明文保存在 env.toml；请在 [dashboard].password 改用 bcrypt 哈希"
        "（以 $2 开头）。当前仅在内存中派生哈希完成校验，明文配置已弃用。"
    )
    if len(stored.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        logger.warning(
            f"Dashboard 明文口令超过 bcrypt 的 {_BCRYPT_MAX_BYTES} 字节上限，"
            f"比较只使用前 {_BCRYPT_MAX_BYTES} 字节；请改用 bcrypt 哈希。"
        )


def verify_password(password: str) -> bool:
    """验证密码：支持 bcrypt 哈希；明文配置在内存中派生哈希后校验。

    明文配置（旧部署）不再参与字符串比较，而是临时派生 bcrypt 哈希后用
    ``bcrypt.checkpw`` 校验，既保持可登录，又避免直接比较明文。
    """
    stored = EnvConfig.DASHBOARD_PASSWORD

    if stored.startswith("$2"):
        return bcrypt.checkpw(_password_bytes(password), stored.encode("utf-8"))

    _warn_legacy_password(stored)
    return bcrypt.checkpw(_password_bytes(password), _derive_legacy_hash(stored))


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = SECURITY_DEPENDENCY,
) -> dict:
    """FastAPI 依赖：从 Authorization header 或 HttpOnly cookie 中提取 JWT token。

    优先级：Authorization header > cookie
    """
    token = credentials.credentials if credentials else None

    # Fallback: read from HttpOnly cookie
    if not token:
        token = request.cookies.get("frontier_token")

    if not token:
        raise HTTPException(status_code=401, detail="缺少认证 token")

    return verify_token(token)


def check_rate_limit(ip: str) -> bool:
    """检查登录频率限制，返回 True 表示允许，False 表示超过限制"""
    now = time.time()
    # 清理过期的记录
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < WINDOW_SECONDS]

    if len(_login_attempts[ip]) >= MAX_ATTEMPTS:
        return False

    _login_attempts[ip].append(now)
    return True
