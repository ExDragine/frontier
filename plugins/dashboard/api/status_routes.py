import os
import platform
import shutil
import time

from fastapi import APIRouter, Depends
from nonebot import get_bots
from sqlmodel import Session, func, select

from utils.configs import EnvConfig
from utils.database import Message, User

from ..auth import require_auth
from ..db import engine

router = APIRouter()

# 记录启动时间
_start_time = time.time()


def get_memory_info():
    """读取 /proc/meminfo 获取系统内存信息（Linux）"""
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])  # in kB
        return {
            "total_mb": mem.get("MemTotal", 0) // 1024,
            "available_mb": mem.get("MemAvailable", 0) // 1024,
            "used_mb": (mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)) // 1024,
            "percent": round((1 - mem.get("MemAvailable", 1) / mem.get("MemTotal", 1)) * 100, 1),
        }
    except Exception:
        return {"total_mb": 0, "available_mb": 0, "used_mb": 0, "percent": 0}


def get_process_memory_mb():
    """读取 /proc/self/status 获取当前进程内存"""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024  # kB -> MB
    except Exception:
        pass
    return 0


@router.get("/overview")
async def get_status_overview(user: dict = Depends(require_auth)):
    """获取 Bot 运行状态概览"""
    bots = get_bots()
    uptime_seconds = int(time.time() - _start_time)

    # 数据库统计
    with Session(engine) as session:
        message_count = session.exec(select(func.count()).select_from(Message)).one()
        user_count = session.exec(select(func.count()).select_from(User)).one()

        # 任务数量（如果 clockwork 插件已加载）
        try:
            from plugins.clockwork.task_models import TaskConfig

            task_count = session.exec(select(func.count()).select_from(TaskConfig)).one()
        except Exception:
            task_count = 0

    return {
        "bot_name": EnvConfig.BOT_NAME,
        "uptime_seconds": uptime_seconds,
        "start_time": int(_start_time),
        "driver": "fastapi+websockets",
        "bot_connected": len(bots) > 0,
        "bot_count": len(bots),
        "features": {
            "agent_module_enabled": EnvConfig.AGENT_MODULE_ENABLED,
            "paint_module_enabled": EnvConfig.PAINT_MODULE_ENABLED,
            "memory_enabled": EnvConfig.MEMORY_ENABLED,
            "agent_capability": EnvConfig.AGENT_CAPABILITY,
            "agent_debug_mode": EnvConfig.AGENT_DEBUG_MODE,
        },
        "models": {
            "basic_model": EnvConfig.BASIC_MODEL,
            "advan_model": EnvConfig.ADVAN_MODEL,
            "paint_model": EnvConfig.PAINT_MODEL,
        },
        "database": {
            "message_count": message_count,
            "user_count": user_count,
            "task_count": task_count,
        },
    }


@router.get("/system")
async def get_system_status(user: dict = Depends(require_auth)):
    """获取系统资源信息"""
    memory = get_memory_info()
    process_memory_mb = get_process_memory_mb()

    # 磁盘使用情况
    disk_usage = shutil.disk_usage("/")

    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory": {
            "total_mb": memory["total_mb"],
            "used_mb": memory["used_mb"],
            "available_mb": memory["available_mb"],
            "percent": memory["percent"],
            "process_mb": process_memory_mb,
        },
        "disk": {
            "total_gb": disk_usage.total // (1024**3),
            "used_gb": disk_usage.used // (1024**3),
            "free_gb": disk_usage.free // (1024**3),
            "percent": round(disk_usage.used / disk_usage.total * 100, 1),
        },
    }
