from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..auth import check_rate_limit, create_token, require_auth, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, body: LoginRequest):
    """用户登录，验证密码并返回 JWT token"""
    # 获取客户端 IP
    client_ip = request.client.host if request.client else "unknown"

    # 检查频率限制
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请 5 分钟后再试")

    # 验证密码
    if not verify_password(body.password):
        raise HTTPException(status_code=401, detail="密码错误")

    # 生成 token
    from utils.configs import EnvConfig

    token = create_token()
    expires_in = EnvConfig.DASHBOARD_JWT_EXPIRE_HOURS * 3600

    return LoginResponse(token=token, expires_in=expires_in)


@router.get("/me")
async def get_current_user(user: dict = Depends(require_auth)):
    """获取当前登录用户信息"""
    return user
