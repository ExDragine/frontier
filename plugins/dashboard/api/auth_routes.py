from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..auth import check_rate_limit, create_token, require_auth, verify_password

router = APIRouter()
AUTH_DEPENDENCY = Depends(require_auth)

# Cookie 安全配置
COOKIE_NAME = "frontier_token"
COOKIE_MAX_AGE = 86400  # 24 小时（与 JWT 过期时间对齐）


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    """Token 同时通过 HttpOnly cookie 和响应体返回。

    前端应优先使用 cookie（自动携带，防 XSS），响应体中的 token
    仅作为降级方案（当客户端不支持 cookie 时）。
    """

    token: str
    expires_in: int


def _set_auth_cookie(response: JSONResponse, token: str, max_age: int) -> None:
    """设置 HttpOnly + Secure + SameSite 认证 cookie。"""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=False,  # 部署 TLS 后改为 True
        samesite="strict",
        path="/api/dashboard",
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, body: LoginRequest):
    """用户登录，验证密码并返回 JWT token。"""
    client_ip = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请 5 分钟后再试")

    if not verify_password(body.password):
        raise HTTPException(status_code=401, detail="密码错误")

    from utils.configs import EnvConfig

    token = create_token()
    expires_in = EnvConfig.DASHBOARD_JWT_EXPIRE_HOURS * 3600

    response = JSONResponse(
        content={"token": token, "expires_in": expires_in}
    )
    _set_auth_cookie(response, token, expires_in)
    return response


@router.get("/me")
async def get_current_user(user: dict = AUTH_DEPENDENCY):
    """获取当前登录用户信息。"""
    return user


@router.post("/logout")
async def logout():
    """清除认证 cookie。"""
    response = JSONResponse(content={"message": "已登出"})
    response.delete_cookie(key=COOKIE_NAME, path="/api/dashboard")
    return response
