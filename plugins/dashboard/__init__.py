from pathlib import Path

from fastapi.staticfiles import StaticFiles
from nonebot import get_app, get_driver, logger

from .api import router as api_router

driver = get_driver()


@driver.on_startup
async def mount_dashboard():
    """挂载 Dashboard 插件到 FastAPI 应用"""
    app = get_app()

    # 挂载 API 路由
    app.include_router(api_router, prefix="/api/dashboard")

    # 挂载静态文件（前端）
    web_dir = Path(__file__).parent / "web"
    app.mount("/dashboard", StaticFiles(directory=str(web_dir), html=True), name="dashboard")

    logger.success("Dashboard 插件已加载：访问 http://localhost:8080/dashboard")
