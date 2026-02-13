import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_auth

router = APIRouter()


class TriggerUpdate(BaseModel):
    trigger_type: str  # "cron" or "interval"
    trigger_args: dict


class GroupsUpdate(BaseModel):
    group_ids: list[int]


@router.get("/")
async def list_tasks(
    enabled: Optional[bool] = None,
    keyword: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """列出所有任务"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    tasks = await task_manager.list_tasks(enabled=enabled, keyword=keyword)

    result = []
    for task in tasks:
        groups = await task_manager.get_task_groups(task.job_id)
        result.append(
            {
                "job_id": task.job_id,
                "name": task.name,
                "description": task.description,
                "trigger_type": task.trigger_type,
                "trigger_args": json.loads(task.trigger_args),
                "enabled": task.enabled,
                "total_runs": task.total_runs,
                "success_runs": task.success_runs,
                "failed_runs": task.failed_runs,
                "last_run_time": task.last_run_time,
                "next_run_time": task.next_run_time,
                "groups": groups,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
        )

    return {"tasks": result, "count": len(result)}


@router.get("/{job_id}")
async def get_task(job_id: str, user: dict = Depends(require_auth)):
    """获取单个任务详情"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    task = await task_manager.get_task(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    groups = await task_manager.get_task_groups(job_id)

    return {
        "job_id": task.job_id,
        "name": task.name,
        "description": task.description,
        "handler_module": task.handler_module,
        "handler_function": task.handler_function,
        "trigger_type": task.trigger_type,
        "trigger_args": json.loads(task.trigger_args),
        "enabled": task.enabled,
        "misfire_grace_time": task.misfire_grace_time,
        "total_runs": task.total_runs,
        "success_runs": task.success_runs,
        "failed_runs": task.failed_runs,
        "last_run_time": task.last_run_time,
        "next_run_time": task.next_run_time,
        "groups": groups,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.put("/{job_id}/enable")
async def enable_task(job_id: str, user: dict = Depends(require_auth)):
    """启用任务"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    # 先检查任务是否存在
    task = await task_manager.get_task(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    success = await task_manager.enable_task(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="启用任务失败，请查看日志")

    return {"message": "任务已启用", "job_id": job_id}


@router.put("/{job_id}/disable")
async def disable_task(job_id: str, user: dict = Depends(require_auth)):
    """禁用任务"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    # 先检查任务是否存在
    task = await task_manager.get_task(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    success = await task_manager.disable_task(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="禁用任务失败，请查看日志")

    return {"message": "任务已禁用", "job_id": job_id}


@router.put("/{job_id}/trigger")
async def update_trigger(job_id: str, body: TriggerUpdate, user: dict = Depends(require_auth)):
    """修改任务触发器"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    success = await task_manager.update_task_trigger(job_id, body.trigger_type, body.trigger_args)
    if not success:
        raise HTTPException(status_code=400, detail="更新触发器失败")

    return {"message": "触发器已更新", "job_id": job_id}


@router.put("/{job_id}/groups")
async def update_groups(job_id: str, body: GroupsUpdate, user: dict = Depends(require_auth)):
    """修改任务推送群组"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    success = await task_manager.update_task_groups(job_id, body.group_ids)
    if not success:
        raise HTTPException(status_code=400, detail="更新群组失败")

    return {"message": "群组配置已更新", "job_id": job_id}


@router.get("/{job_id}/history")
async def get_history(job_id: str, limit: int = Query(default=50, ge=1, le=500), user: dict = Depends(require_auth)):
    """获取任务执行历史"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    history = await task_manager.get_execution_history(job_id=job_id, limit=limit)

    return {
        "history": [
            {
                "id": h.id,
                "execution_time": h.execution_time,
                "status": h.status,
                "duration_ms": h.duration_ms,
                "error_message": h.error_message,
                "groups_sent": json.loads(h.groups_sent) if h.groups_sent else [],
                "messages_sent": h.messages_sent,
                "scheduled_time": h.scheduled_time,
            }
            for h in history
        ],
        "count": len(history),
    }


@router.get("/{job_id}/stats")
async def get_stats(job_id: str, user: dict = Depends(require_auth)):
    """获取任务统计信息"""
    try:
        from plugins.clockwork import task_manager
    except ImportError:
        raise HTTPException(status_code=503, detail="任务管理系统未加载")

    stats = await task_manager.get_task_statistics(job_id)
    if not stats:
        raise HTTPException(status_code=404, detail="任务不存在")

    return stats
